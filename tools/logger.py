class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[0;34m'
    CYAN = '\033[96m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    RED = '\033[0;31m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'


def log_processing(msg):
    print(f'{bcolors.BLUE}🔨 {msg}{bcolors.ENDC}')


def log_info(msg):
    print(f'{bcolors.BLUE}ℹ️  {msg}{bcolors.ENDC}')


def log_error(msg):
    print(f'{bcolors.RED}❌ {msg}{bcolors.ENDC}')


def log_ok(msg):
    print(f'{bcolors.GREEN}✅ {msg}{bcolors.ENDC}')


def log_warning(msg):
    print(f'{bcolors.YELLOW}⚠️  {msg}{bcolors.ENDC}')


def log_success(msg):
    print(f'{bcolors.GREEN}{bcolors.UNDERLINE}🎉 {msg}{bcolors.ENDC}')
