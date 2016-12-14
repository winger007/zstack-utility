import timeimport threadingfrom zstacklib.utils import shellimport subprocessimport osimport tracebackfrom zstacklib.utils import logfrom zstacklib.utils import threadfrom zstacklib.utils.report import Reportlogger = log.get_logger(__name__)class WatchThread(threading.Thread):    def __init__(self, fpread, popen, processType, uuid):        threading.Thread.__init__(self)        self.fpread = fpread        self.popen = popen        self.keepRunning = True        self.total = 0        self.processType = processType        self.resourceUuid = uuid    def run(self):        self._report("10", "start")        while self.keepRunning and self.popen and self.popen.poll() is None:            line = str(self.fpread.readlines()).strip()            synced = 0            logger.debug(line)            lines = line.split()            logger.debug("line: %s, synced: %s, total: %s", line, synced, self.total)            try:                if len(lines) > 3 and self.total > 0:                    logger.debug("lines[1]: %s", lines[1])                    synced += long(lines[1])                    if synced < self.total:                        percent = int(round(float(synced) * 100 / float(self.total) * 0.8 + 10))                    else:                        break                    self._report(percent, "reports")                else:                    pass            except Exception as e:                logger.debug("ignore the exception: %s", e.message)                pass            time.sleep(1)        self._report("90", "finish")    def stop(self):        self.keepRunning = False        self.fpread.close()    def setTotal(self, total):        self.total = total    def _report(self, percent):        self._report(self, percent, "reports")    def _report(self, percent, flag):        logger.debug("progress is: %s", percent)        self._progress_report(percent, flag)    def _progress_report(self, percent, flag):        try:            reports = Report()            reports.progress = percent            reports.processType = self.processType            header = {                "start": "/progress/start",                "finish": "/progress/finish",                "reports": "/progress/reports"            }            reports.header = {'commandpath': header.get(flag, "/progress/reports")}            reports.resourceUuid = self.resourceUuid            reports.report()        except Exception as e:            content = traceback.format_exc()            logger.warn(content)            logger.warn("report progress failed: %s", e.message)def main():    test_out = shell.call('mktemp /tmp/tmp-XXXXXX').strip()    fpwrite = open(test_out, 'w')    p = subprocess.Popen('/bin/bash', stdout=fpwrite, stdin=subprocess.PIPE, stderr=subprocess.PIPE)    watch = WatchThread(p, open(test_out, 'r'))    watch.start()    _, e = p.communicate('ping -c 10 114.114.114.114')    r = p.returncode    watch.stop()    fpwrite.close()    os.remove(test_out)    if r != 0:        print "error return: %s", rif __name__ == "__main__":    main()