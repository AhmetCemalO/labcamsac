import sys
from argparse import ArgumentParser
from PyQt5.QtWidgets import QApplication
from view.widgets import LabcamsWindow
from utils import get_preferences, display

def main():
    """
    Parses the arguments, gets preferences and calls GUI_initializer
    """
    parser = ArgumentParser(description='Labcams: multiple camera control and recording.')
    parser.add_argument('-p','--pref',metavar='preference',
                        type=str,help='Preference filename',default = None)
    args = parser.parse_args()

    ret, prefs = get_preferences(args.pref)
    
    if not ret:
        display('Warning: could not load preferences')

    app = QApplication(sys.argv)
    w = LabcamsWindow(preferences = prefs)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()