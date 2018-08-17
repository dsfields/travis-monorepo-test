import os
import shutil
import subprocess
import sys
import warnings


CONFIG_DIR = '.monorepo'
IGNORE_FILE = 'ignore'
BUILD_SCRIPT = 'build.sh'
DEPLOY_SCRIPT = 'deploy.sh'
CWD = os.getcwd()
CONFIG_PATH = os.path.join(CWD, CONFIG_DIR)
DEFAULT_BUILD_PATH = os.path.join(CONFIG_PATH, BUILD_SCRIPT)
DEFAULT_DEPLOY_PATH = os.path.join(CONFIG_PATH, DEPLOY_SCRIPT)
HAS_CONFIG = os.path.isdir(CONFIG_PATH)
HAS_DEFAULT_BUILD = os.path.isfile(DEFAULT_BUILD_PATH)
HAS_DEFAULT_DEPLOY = os.path.isfile(DEFAULT_DEPLOY_PATH)


def info(msg):
    print >>sys.stdout, 'INFO: %s' % (msg)


def warning(msg):
    print >>sys.stdout, 'WARNING: %s' % (msg)


def error(msg):
    print >>sys.stderr, 'ERROR: %s' % (msg)


def query_git():
    result = subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', os.environ['TRAVIS_COMMIT']])
    return result.split('\n')


def find_todo(ignored):
    todo = { 'build': set(), 'deploy': set() }
    changed = query_git()

    for i, file_name in enumerate(changed):
        if file_name in ignored:
            continue

        path_parts = file_name.split('/')

        if len(path_parts) < 2:
            continue

        change_type = path_parts[1]

        if change_type == 'src' or change_type == 'build.sh':
            todo.get('build').add(path_parts[0])
            todo.get('deploy').add(path_parts[0])
            continue

        if change_type == 'config' or change_type == 'deploy.sh':
            todo.get('deploy').add(path_parts[0])

    return todo


def load_ignore():
    ignore_path = os.path.join(CONFIG_PATH, IGNORE_FILE)
    if not HAS_CONFIG or os.path.exists(ignore_path):
        return set()

    with open(ignore_path, 'r') as ig:
        ignore = set()
        for line in ig:
            ignore.add(line.strip())

        return ignore


def execute(changed, script, default_script, has_default):
    for i, dir_name in enumerate(changed):
        file_name = os.path.join(CWD, dir_name, script)

        if not os.path.isfile(file_name):
            if not has_default:
                warning('No "%s" found for "%s"' % (script, dir_name))
                continue
            shutil.copyfile(default_script, file_name)

        result = subprocess.call(['sh', file_name])

        if result != 0:
            error('Failure encountered running: %s' % (file_name))
            return False

    return True


def main():
    info('Beginning monorepo build')
    ignore = load_ignore()
    todo = find_todo(ignore)
    success = execute(todo.get('build'), BUILD_SCRIPT, DEFAULT_BUILD_PATH, HAS_DEFAULT_BUILD)

    if success:
        success = execute(todo.get('deploy'), DEPLOY_SCRIPT, DEFAULT_DEPLOY_PATH, HAS_DEFAULT_DEPLOY)

    if success:
        info('Monorepo build completed successfully')
        sys.exit(0)
    else:
        info('Monorepo build completed with errors')
        sys.exit(1)


if __name__ == '__main__':
    main()
