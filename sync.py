
import sys
import os
import larg
from latus import logger, settings, sync

if __name__ == "__main__":
    logger.setup()
    log = logger.get_log()

    epi = ["Examples:",\
           os.path.split(sys.argv[0])[-1] + " -r                                       # do sync using default location for settings",
           os.path.split(sys.argv[0])[-1] + " -r -o C:\\joe\\latus\\settings\\             # explicitly specify settings folder",
           os.path.split(sys.argv[0])[-1] + " -d                                       # dump settings",
           os.path.split(sys.argv[0])[-1] + " -s local C:\\Users\\joe\\Documents\\latus\\   # set local folder",
           os.path.split(sys.argv[0])[-1] + " -s cloud C:\\Users\\joe\\Documents\\DropBox\\ # set cloud storage folder"]

    parser = larg.init("latus folder sync")
    parser.add_argument("-r", "--run", action="store_true", help="run the sync")
    parser.add_argument("-o", "--override", metavar='path', help="override path to settings folder")
    parser.add_argument("-d", "--dump", action="store_true", help="print settings information")
    parser.add_argument("-s", "--set", nargs=2, metavar=('key','value'), help="assign a value to a particular setting")

    args = larg.parse_args(parser, epi)
    logger.set_log_level(args.loglevel)

    settings_section = 'latus'
    user_settings = settings.Settings(args.override)

    if args.set:
        user_settings.set(settings_section, args.set[0], args.set[1])
    if args.dump:
        all_settings = user_settings.get_all()
        for setting in all_settings[settings_section]:
            print("%s = %s" % setting) # make it look like the .ini file format
    if args.run:

        # *** do some basic settings checks. ***
        # first, make sure what we need is set to something
        setting_required_folders = ['cloud', 'local']
        for setting_required_folder in setting_required_folders:
            if not user_settings.get(settings_section, setting_required_folder):
                exit("error : setting '%s' not set (use -s to set, -h for help)" % setting_required_folder)
        # cloud folder should already exist
        cloud_folder = user_settings.get(settings_section, 'cloud')
        if not os.path.exists(cloud_folder):
            exit("error : folder %s does not exist (check 'cloud' setting or -h for help)" % cloud_folder)
        # create local folder if it doesn't exist
        local_folder = user_settings.get(settings_section, 'local')
        if not os.path.exists(local_folder):
            print("creating %s" % local_folder)
            os.makedirs(local_folder)

        do_sync = sync.sync(args.override, args.verbose)
        do_sync.run()
    elif not args.set and not args.dump:
        print("nothing to do")
        print("-h for help")

