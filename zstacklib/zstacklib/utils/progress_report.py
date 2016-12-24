import time
import threading
from zstacklib.utils import shell
import subprocess
import os
import traceback
from zstacklib.utils import log
from zstacklib.utils import thread
from zstacklib.utils.report import Report
from zstacklib.utils.report import Progress


logger = log.get_logger(__name__)

class WatchThread(threading.Thread):
    def __init__(self, fpread, popen, progress=None):
        threading.Thread.__init__(self)
        self.fpread = fpread
        self.popen = popen
        self.keepRunning = True
        self.progress = progress if progress else Progress()

    def setProgress(self, progress):
        self.progress = progress

    def run(self):
        logger.debug("watch thread start...")
        start, end = self.progress.getScale()
        self._progress_report(start, self.progress.getStart())
        while self.keepRunning and self.popen and self.popen.poll() is None:
            line = str(self.fpread.readlines()).strip()
            synced = 0
            logger.debug(line)
            lines = line.split()
            logger.debug("line: %s, synced: %s, total: %s", line, synced, self.progress.total)
            try:
                if len(lines) > 1 and self.progress.total > 0:
                    logger.debug("lines[1]: %s", lines[1])
                    synced += long(lines[1])
                    if synced < self.progress.total:
                        percent = start if start == end \
                            else int(round(float(synced) / float(self.progress.total) * (end - start) + start))
                        self._progress_report(percent, self.progress.getReport())
                else:
                    pass
            except Exception as e:
                # sometimes the line is not illegal, we cannot stop the action
                logger.debug("ignore the exception: %s", e.message)
                pass
            time.sleep(1)
        self._progress_report(end, self.progress.getEnd())

    def stop(self):
        self.keepRunning = False
        self.fpread.close()

    def _report(self, percent):
        self._progress_report(self, percent, self.progress.getReport())

    def _progress_report(self, percent, flag):
        logger.debug("progress is: %s", percent)
        try:
            reports = Report()
            reports.progress = percent
            reports.processType = self.progress.processType
            header = {
                "start": "/progress/start",
                "finish": "/progress/finish",
                "report": "/progress/report"
            }
            reports.header = {'commandpath': header.get(flag, "/progress/report")}
            reports.resourceUuid = self.progress.resourceUuid
            reports.report()
        except Exception as e:
            content = traceback.format_exc()
            logger.warn(content)
            logger.warn("report progress failed: %s", e.message)


def main():
    test_out = shell.call('mktemp /tmp/tmp-XXXXXX').strip()
    fpwrite = open(test_out, 'w')
    p = subprocess.Popen('/bin/bash', stdout=fpwrite, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    watch = WatchThread(p, open(test_out, 'r'))
    watch.start()
    _, e = p.communicate('ping -c 10 114.114.114.114')
    r = p.returncode
    watch.stop()
    fpwrite.close()
    os.remove(test_out)
    if r != 0:
        print "error return: %s", r

if __name__ == "__main__":
    main()

