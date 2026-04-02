# -*- encoding: utf-8 -*-
'''
@Time     :   2026/01/22 22:09:49
@Author   :   QuYue
@File     :   Logger.py
@Email    :   quyue1541@gmail.com
@Desc:    :   Logger
'''


#%% Import Packages
import os
import sys
import logging
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler


# @dataclass
# class WandbConfig:
#     project: str
#     name: Optional[str] = None
#     entity: Optional[str] = None
#     group: Optional[str] = None
#     job_type: Optional[str] = None
#     tags: Optional[list[str]] = None
#     notes: Optional[str] = None
#     config: Optional[dict] = None
#     mode: Optional[str] = None  # "online" | "offline" | "disabled"


#%% Handler
# Filters: Log file
class FileFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # 默认：输出到 file（True）
        return bool(getattr(record, "to_file", True))

# Filters: Console
class ConsoleFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # 默认：输出到 console（True）
        return bool(getattr(record, "to_console", True))
    
# Console handler that can work with tqdm
class TqdmHandler(logging.Handler):
    """
    A console handler that plays nicely with tqdm (won't break progress bars).
    If tqdm is not installed, it falls back to stdout.
    """
    _tqdm = None  # class-level cache
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if TqdmHandler._tqdm is None:
                try:
                    from tqdm import tqdm
                    TqdmHandler._tqdm = tqdm
                except Exception:
                    TqdmHandler._tqdm = False  # sentinel: tqdm not available
            if TqdmHandler._tqdm:
                TqdmHandler._tqdm.write(msg)
            else:
                sys.stdout.write(msg + "\n")
        except Exception:
            self.handleError(record)

#  Formatter that can switch formatters
class FormatterHandler(logging.Handler):
    """
    A handler that can switch formatter per record using record.simple flag.
    """
    def __init__(self, base_handler: logging.Handler,
                 formatter_full: logging.Formatter,
                 formatter_simple: logging.Formatter):
        super().__init__(base_handler.level)
        self.base_handler = base_handler
        self.formatter_full = formatter_full
        self.formatter_simple = formatter_simple

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if getattr(record, "simple", False):
                self.base_handler.setFormatter(self.formatter_simple)
            else:
                self.base_handler.setFormatter(self.formatter_full)
            self.base_handler.emit(record)
        except Exception:
            self.handleError(record)


#%% Logger
class Logger:
    """
    Logger class for logging messages to console, file, and remote services (e.g., wandb).
    Supports different log levels and flexible output options.
    """

    def __init__(self, 
                 name: str = "logger",
                 log_path: Optional[str] = None,
                 max_bytes: int = 10 * 1024 * 1024, # max size of log file
                 backup_count: int = 5,             # number of rotated log files to keep
                 ):
        """
        Create a unified logger with console and optional rotating file output.

        Parameters
        ----------
        name : str, optional, default="logger"
            Logical name of the logger instance (used for identification).

        log_path : str or None, optional, default=None
            Path to the log file. If None, file logging is disabled.

        max_bytes : int, optional, default=10 * 1024 * 1024
            Maximum size (in bytes) of a single log file before rotation.

        backup_count : int, optional, default=5
            Number of rotated log files to keep.

        Notes
        -----
        - Console and file outputs are independently controllable per log record.
        - Log files are automatically rotated when exceeding `max_bytes`.
        """
        # config
        self.name = name
        self.log_path = log_path
        self.remote = None
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # create log file
        if self.log_path is not None:
            log_dir = os.path.dirname(self.log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

        # create core logger
        self.logger = logging.getLogger(f"{self.__class__.__name__}:{self.name}:{id(self)}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False # prevent double logging
        self.logger.handlers.clear()
        self.formatter_full = logging.Formatter(
            # fmt="%(asctime)s [ %(levelname)-7s ] %(message)s",
            fmt="%(asctime)s [ %(levelname)s ] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.formatter_simple = logging.Formatter(
            fmt="%(message)s",
        )

        # logging -> file
        if self.log_path is not None:
            fh = RotatingFileHandler(
                self.log_path,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            fh.setLevel(logging.INFO)
            fh.addFilter(FileFilter())
            fh = FormatterHandler(
                fh,
                formatter_full=self.formatter_full,
                formatter_simple=self.formatter_simple,
            )
            self.logger.addHandler(fh)
        
        # logging -> console
        # ch = TqdmHandler() # tqdm safe console handler
        ch = logging.StreamHandler(sys.stdout)
        # ch.setLevel(logging.INFO)
        ch.setLevel(logging.DEBUG)
        ch.addFilter(ConsoleFilter())   # 👈 只放行 to_console=True
        ch = FormatterHandler(
            ch,
            formatter_full=self.formatter_full,
            formatter_simple=self.formatter_simple,
        )
        self.logger.addHandler(ch)

    def set_remote(self, remote: Optional[str] = None, project: Optional[str] = None, **kwargs):
        """
        Enable and configure a remote logging backend.

        Currently supports:
        - "wandb": Weights & Biases logging

        Parameters
        ----------
        remote : str or None
            Name of the remote logging backend (e.g., "wandb").

        project : str or None
            Project name for the remote backend. If None, defaults to logger name.

        **kwargs
            Configuration options forwarded to the remote backend initializer.

            For "wandb", commonly used options include:
            - api_key : str, optional
                Weights & Biases API key. If None, environment variable
                WANDB_API_KEY is used.
            - name : str, optional
                Run name.
            - entity : str, optional
                W&B entity (user or team).
            - group : str, optional
                Group name for organizing runs.
            - tags : list[str], optional
                List of tags for the run.
            - notes : str, optional
                Notes or description for the run.
            - config : dict, optional
                Experiment configuration dictionary.
            - mode : str, optional
                "online", "offline", or "disabled".

        Notes
        -----
        - Remote logging is optional and failure-tolerant.
        - Initialization errors will be logged locally and will not
        crash the main process.
        - Additional keyword arguments are passed directly to the
        backend initializer (e.g., wandb.init()).
        """
        # logging -> remote (wandb)
        project = project if project is not None else self.name
        if remote == "wandb":
            try:
                self.remote_plugin = Wandb_plugin(project=project, **kwargs)
            except Exception as e:
                self.error(f"wandb init failed. {e}", console=True, file=True)
        else:
            self.error(f"Unsupported remote logger: {remote}", console=True, file=True)
        self.remote = remote

    
    # --------------------
    # ----- Logging 
    # --------------------
    def print(self, *items: Any, sep: str = " ", end: str = "", flush: bool = False, console: bool = True, file: bool = True, simple: bool = False, ptype: str = "info",  **kwargs):
        """
        Print-like logging interface.

        This method mimics the built-in `print()` function and routes
        the output to the logger with a specified log level.

        Parameters
        ----------
        *items : Any
            Objects to be printed. They are converted to strings and joined.

        sep : str, optional, default=" "
            Separator between items (same as built-in print).

        end : str, optional, default=""
            String appended after the last item.

        flush : bool, optional, default=False
            Whether to flush stdout immediately.

        console : bool, optional, default=True
            Whether to output the message to the console.

        file : bool, optional, default=True
            Whether to write the message to the log file.

        simple : bool, optional, default=False
            If True, use simple formatting (message only).
            If False, use full formatting (timestamp + level + message).

        ptype : str, optional, default="info"
            Log type used to route the message. One of:
            {"info", "debug", "warning", "error", "exception"}.

        **kwargs
            Additional keyword arguments forwarded to the underlying
            logging call.
        """
        text = sep.join(str(x) for x in items) + end
        if flush:
            sys.stdout.flush()
        if ptype == "info":
            self.info(text,console=console,file=file,simple=simple,**kwargs)
        elif ptype == "debug":
            self.debug(text,console=console,file=file,simple=simple,**kwargs)
        elif ptype == "warning":
            self.warning(text,console=console,file=file,simple=simple,**kwargs)
        elif ptype == "error":
            self.error(text,console=console,file=file,simple=simple,**kwargs)
        elif ptype == "exception":
            self.exception(text,console=console,file=file,simple=simple,**kwargs)
        else:
            raise ValueError(f"Unsupported print type: {ptype}")
    
    def log_metrics(self, 
                    data: Dict[str, Any],
                    msg: Optional[str] = None,
                    remote: bool = False,
                    console: bool = True,
                    file: bool = True,
                    simple: bool = False,
                    step: Optional[int] = None,
                    commit: bool = True) -> None:

        """
        Log a dictionary of metrics locally and optionally to a remote backend.

        Metrics are formatted into a readable log line and written to the
        local logger. They can also be forwarded to a remote logging backend
        (e.g., Weights & Biases).

        Parameters
        ----------
        data : dict
            Dictionary of metric names and values.

        msg : str or None, optional, default=None
            Custom log message. If None, a message is auto-generated
            from the metric dictionary.

        remote : bool, optional, default=False
            Whether to forward the metrics to the remote backend.

        console : bool, optional, default=True
            Whether to log the message to the console.

        file : bool, optional, default=True
            Whether to log the message to the log file.

        simple : bool, optional, default=False
            If True, use simple formatting (message only).
            If False, use full formatting (timestamp + level + message).

        step : int or None, optional, default=None
            Step number associated with the metrics for remote logging.

        commit : bool, optional, default=True
            Whether to finalize and upload the step for remote logging.

        Notes
        -----
        - If `msg` is None, metrics are auto-formatted into a readable string.
        - Remote logging is optional and failure-tolerant.
        """
        # logging -> local (file)
        if msg is None:
            text = ''
            for k, v in data.items():
                text += f"| {k}={v:.2f} "
            text = text.strip()[1:]  # remove leading '|'
        else:
            text = msg
        self.info(text, console=console, file=file, simple=simple)

        # logging -> remote
        if remote:
            self.remote_log(data, step=step, commit=commit) 

    def info(self, msg: str, *args, console: bool = True, file: bool = True, simple: bool = False, **kwargs):
        """
        Log an informational message.

        The message is routed to the console and/or log file based on
        the `console` and `file` flags.

        Parameters
        ----------
        msg : str
            Log message format string.

        *args : Any
            Arguments used for message formatting.

        console : bool, optional, default=True
            Whether to output the message to the console.

        file : bool, optional, default=True
            Whether to write the message to the log file.

        simple : bool, optional, default=False
            If True, use simple formatting (message only).
            If False, use full formatting (timestamp + level + message).

        **kwargs
            Additional keyword arguments forwarded to the underlying
            logging call.
        """
        self.logger.info(
            msg, *args,
            extra={"to_console": console, "to_file": file, "simple": simple},
            **kwargs
            )
        
    def debug(self, msg: str, *args, console: bool = True, file: bool = True, simple: bool = False, **kwargs):
        """
        Log a debug-level message.

        Parameters
        ----------
        msg : str
            Log message format string.

        *args : Any
            Arguments used for message formatting.

        console : bool, optional
            Whether to output the message to the console.

        file : bool, optional
            Whether to write the message to the log file.

        simple : bool, optional
            If True, use simple formatting (message only).
            If False, use full formatting (timestamp + level + message).

        **kwargs
            Additional keyword arguments forwarded to the underlying
            logging call.
        """
        self.logger.debug(
            msg, *args,
            extra={"to_console": console, "to_file": file, "simple": simple},
            **kwargs
            )
    
    def warning(self, msg: str, *args, console: bool = True, file: bool = True, simple: bool = False, **kwargs):
        """
        Log a debug-level message.

        Parameters
        ----------
        msg : str
            Log message format string.

        *args : Any
            Arguments used for message formatting.

        console : bool, optional, default=True
            Whether to output the message to the console.

        file : bool, optional, default=True
            Whether to write the message to the log file.

        simple : bool, optional, default=False
            If True, use simple formatting (message only).
            If False, use full formatting (timestamp + level + message).

        **kwargs
            Additional keyword arguments forwarded to the underlying
            logging call.
        """
        self.logger.warning(
            msg, *args,
            extra={"to_console": console, "to_file": file, "simple": simple},
            **kwargs
            )
    
    def error(self, msg: str, *args, console: bool = True, file: bool = True, simple: bool = False, ifbreak=False, **kwargs):
        """
        Log an error-level message.

        Parameters
        ----------
        msg : str
            Log message format string.

        *args : Any
            Arguments used for message formatting.

        console : bool, optional, default=True
            Whether to output the message to the console.

        file : bool, optional, default=True
            Whether to write the message to the log file.

        simple : bool, optional, default=False
            If True, use simple formatting (message only).
            If False, use full formatting (timestamp + level + message).

        **kwargs
            Additional keyword arguments forwarded to the underlying
            logging call.
        """
        self.logger.error(
            msg, *args,
            extra={"to_console": console, "to_file": file, "simple": simple},
            **kwargs
            )
        if ifbreak:
            raise RuntimeError(msg)
        
    
    def exception(self, msg: str, *args, console: bool = True, file: bool = True, simple: bool = False, **kwargs):
        """
        Log an exception with traceback information.

        This method should be called inside an `except` block.
        If an active exception is present, the traceback is included
        in the log output.

        Parameters
        ----------
        msg : str
            Log message format string.

        *args : Any
            Arguments used for message formatting.

        console : bool, optional, default=True
            Whether to output the message to the console.

        file : bool, optional, default=True
            Whether to write the message to the log file.

        simple : bool, optional, default=False
            If True, use simple formatting (message only).
            If False, use full formatting (timestamp + level + message).

        **kwargs
            Additional keyword arguments forwarded to the underlying
            logging call.

        Notes
        -----
        - If called outside of an `except` block, no traceback
        information will be included.
        """
        self.logger.exception(
            msg, *args,
            extra={"to_console": console, "to_file": file, "simple": simple},
            **kwargs
            )

    def remote_log(self, 
                   data: Dict[str, Any],
                   step: Optional[int] = None,
                   commit: bool = True) -> None:
        """
        Log data to the configured remote logging backend.

        This method forwards the given data dictionary to the active
        remote logging plugin (e.g., Weights & Biases).

        Parameters
        ----------
        data : dict
            Dictionary of key-value pairs to be logged remotely.

        step : int or None, optional, default=None
            Step number associated with the data for remote logging.

        commit : bool, optional, default=True
            Whether to finalize and upload the step for remote logging.

        Notes
        -----
        - If no remote backend is configured, this method does nothing.
        - Remote logging is failure-tolerant: errors are caught and
        reported locally as warnings.
        """
        results = None
        if self.remote:
            results = self.remote_plugin.log(data, step=step, commit=commit)
        if results is not None:
            self.warning(f"Remote logging failed. {results}", console=True, file=True)

    def __str__(self) -> str:
        """
        Human-readable summary of the logger configuration.
        """
        parts = [
            f"name={self.name!r}",
            f"log_path={self.log_path!r}",
            f"remote={self.remote!r}",
        ]

        return f"Logger({', '.join(parts)})"


    def __repr__(self) -> str:
        """
        Unambiguous representation for debugging.
        """
        return self.__str__()
        
#%%
class Wandb_plugin:
    def __init__(self, **kwargs):
        try:
            import wandb  # lazy import
            self.wandb = wandb
        except ImportError as e:
            raise ImportError("wandb is not installed. `pip install wandb`") from e
        self.init(**kwargs)

    def init(self, api_key: Optional[str] = None, project: str = 'my-project', **kwargs):
        try:
            if api_key is not None:
                self.wandb.login(key=api_key, relogin=True)
        except Exception:
            raise f"wandb login failed. {Exception}"
        self.wandb.init(project=project, **kwargs)

    def log(self, data: Dict[str, Any], step: Optional[int] = None, commit: bool = True) -> None:
        try:
            self.wandb.log(data, step=step, commit=commit)
            return None
        except Exception:
            return Exception


#%%
if __name__ == "__main__":
    logger = Logger(log_path="test.log", name="test_logger")
    logger.info("This is an info message.", console=True, file=True)
    logger.debug("This is a debug message.", console=True, file=True)
    logger.warning("This is a warning message.", console=True, file=True)
    logger.error("This is an error message.", console=True, file=True)
    try:
        1 / 0
    except Exception:
        logger.exception("This is an exception message.", console=True, file=True)

    metrics = {"accuracy": 0.95, "loss": 0.05}
    logger.log_metrics(metrics, remote=True, console=True, file=True, simple=False)
    
#%%
    logger.set_remote(remote="wandb", project="test_project")
    logger.log_metrics({"epoch": 1, "accuracy": 0.98}, remote=True, step=1)
