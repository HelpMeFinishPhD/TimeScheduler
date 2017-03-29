#!/usr/bin/env python
"""
    Scheduler GUI : Log down time spent on (probably) uncessarys stuffs
    Copyright (C) 2017 Adrian Utama

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Run from current working directory (if you created symlink thingy)
import os
realpath = os.path.realpath(__file__)
dname = os.path.dirname(realpath)
os.chdir(dname)

import sys
import glob
import datetime

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QTimer

REFRESH_RATE = 1000  #1s, i.e. don't need to refresh too frequently
form_class = uic.loadUiType("gui.ui")[0]

class MyWindowClass(QtGui.QMainWindow, form_class):

    def __init__(self, parent=None):

        # Program is starting
        self.running = 1
        self.started = 0    # Bind to buttons

        # Declaring GUI window
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.initialiseParameters()

        # Set timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.setInterval(REFRESH_RATE)
        self.timer.start()

    def initialiseParameters(self):

        # Read task config file
        task = [line.rstrip('\n') for line in open('task.conf')]
        self.chooseTask.addItems(task)

        # Bind buttons
        self.startStop.clicked.connect(self.handleStartStop)

    def update(self):

        # Update current time
        now = datetime.datetime.now()
        year, week, day = now.isocalendar()
        day_label = "Year " + str(year) + "   Week " + str(week) + "   Day " + str(day)
        time_label = str(now.time())[:8]    # Remove the microsecond nonsenses
        self.labelDay.setText(day_label)
        self.labelTime.setText(time_label)

        # Update labelElapsed
        if self.started == 0:
            self.labelElapsed.setText("OFF")
        elif self.started == 1:
            time_elapsed = now - self.time_started
            time_elapsed_label = str(time_elapsed.__str__())[:7]    # Remove the microsecond nonsenses
            self.labelElapsed.setText(time_elapsed_label)

        # Get correct filename (overflow to the next week)
        self.logfile = "log/log_" + str(year) + "_" + str(week)     # Log file classified wrt week

        # Get and log stuffs from logfile
        try:
            with open(self.logfile, 'r') as f:
                logged = f.readlines()

            # Process the logfile. I am lazy, so I parse each pairs of the lines manually
            proc = 0   # Looking for started
            collated = []
            for lines in logged:
                info = lines.split(",") # First element is time, second element is STARTED/STOPPED, and the third element is the type of activity
                if proc == 0 and info[1] == "STARTED":    # Falls into STARTED trap
                    time_started = datetime.datetime.strptime(info[0], '%Y-%m-%d %H:%M:%S.%f')
                    proc = 1
                elif proc == 1 and info[1] == "STOPPED":  # Falls into STOPPED trap
                    proc = 0
                    time_stopped = datetime.datetime.strptime(info[0], '%Y-%m-%d %H:%M:%S.%f')
                    elapsed = time_stopped - time_started
                    collated.append([elapsed, info[2][:-1]])    # Lazy hack to remove "\n"
            if proc == 1:     # If the time is still started
                proc = 0
                time_stopped = now
                elapsed = time_stopped - time_started
                collated.append([elapsed, info[2][:-1]])    # Lazy hack to remove "\n"

            # Refine the collated data
            refined_work = []
            refined_time = []
            for lists in collated:
                try:                    # Lazy hack to insert new type of activities
                    idx = refined_work.index(lists[1])
                    refined_time[idx] += lists[0]
                except ValueError:
                    refined_work.append(lists[1])
                    refined_time.append(lists[0])

            # Modify textLog
            combined_str = "In year " + str(year) + " and week " + str(week) + ", your sacrifices are as follows: \n"
            for idx in range(len(refined_work)):
                time_el = str(refined_time[idx])[:7]
                stuff = refined_work[idx]
                combined_str += str(idx+1) + ". Time spent on " + stuff + " is " + time_el + "\n"

            # Modify the log in the GUI
            self.textLog.setPlainText(combined_str[:-1])    # Lazy hack to remove the last '\n'

        except IOError:
            pass

    def handleStartStop(self):
        if self.started == 0:
            self.time_started = datetime.datetime.now()
            self.started = 1
            self.chooseTask.setEnabled(False)   # So can't change task in between.
            # Writing the starting time to log
            with open(self.logfile, 'a') as f:
                message = str(self.time_started) + ",STARTED," + self.chooseTask.currentText()
                f.write(message + '\n')
            self.startStop.setText("Stop")  # Change button appearance
        elif self.started == 1:
            self.started = 0
            self.chooseTask.setEnabled(True)
            now = datetime.datetime.now()
            # Writing the stopping time to log
            with open(self.logfile, 'a') as f:
                message = str(now) + ",STOPPED," + self.chooseTask.currentText()
                f.write(message + '\n')
            self.startStop.setText("Start")

    def cleanUp(self):
        if self.started == 1:   # To clear the session if closed down, i.e stop them
            self.handleStartStop()
        print "Bye!"


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    myWindow = MyWindowClass(None)
    myWindow.show()
    app.aboutToQuit.connect(myWindow.cleanUp)
    sys.exit(app.exec_())
