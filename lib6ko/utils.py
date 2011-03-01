import time

def log_sleep(timeout, log=None):
    left = timeout
    step = min(0.1, timeout)
    while left > 0:
        if log:
            log.debug("Waiting {0}s".format(step))
        time.sleep(step)
        yield step
        left -= step
        step = min(step*2, left)

