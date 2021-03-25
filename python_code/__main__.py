import sys
from argparse import ArgumentParser
from view.widgets import LabcamsWindow

def main():
    """
    Parses the arguments, gets preferences and calls GUI_initializer
    """
    parser = ArgumentParser(description='Labcams: multiple camera control and recording.')
    parser.add_argument('-p','--pref',metavar='preference',
                        type=str,help='Preference filename',default = None)
    args = parser.parse_args()

    prefsel = args.pref

    prefs = getPreferences(user = user,selection = prefsel)
    
    app = QApplication(sys.argv)
    display('Initializing Labcams GUI')
    w = LabcamsWindow(preferences = prefs)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()