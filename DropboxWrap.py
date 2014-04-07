import locale
import os
import pprint
import shlex
import sys

from dropbox import client, rest, session

class DropboxTerm():
    TOKEN_FILE = "token_store.txt"

    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.current_path = ''
        self.prompt = "Dropbox> "
        self.is_logged_in = False
        self.api_client = None
        try:
            serialized_token = open(self.TOKEN_FILE).read()
            if serialized_token.startswith('oauth2:'):
                access_token = serialized_token[len('oauth2:'):]
                self.api_client = client.DropboxClient(access_token)
                self.is_logged_in = True
                print "[loaded OAuth 2 access token]"
            else:
                print "Malformed access token in %r." % (self.TOKEN_FILE,)
        except IOError:
            pass # don't worry if it's not there
    def is_logged(self):
        return self.is_logged_in
    def ls(self):
        """list files in current remote directory"""
        resp = self.api_client.metadata(self.current_path)
		l = []
        if 'contents' in resp:
            for f in resp['contents']:
                name = os.path.basename(f['path'])
                encoding = locale.getdefaultlocale()[1]
                l.append(('%s\n' % name).encode(encoding))

    def cd(self, path):
        """change current working directory"""
        if path == "..":
            self.current_path = "/".join(self.current_path.split("/")[0:-1])
        else:
            self.current_path += "/" + path

    def login(self):
        """log in to a Dropbox account"""
        flow = client.DropboxOAuth2FlowNoRedirect(self.app_key, self.app_secret)
        authorize_url = flow.start()
        sys.stdout.write("1. Go to: " + authorize_url + "\n")
        sys.stdout.write("2. Click \"Allow\" (you might have to log in first).\n")
        sys.stdout.write("3. Copy the authorization code.\n")
        code = raw_input("Enter the authorization code here: ").strip()
        
        try:
            access_token, user_id = flow.finish(code)
        except rest.ErrorResponse, e:
            self.stdout.write('Error: %s\n' % str(e))
            return

        with open(self.TOKEN_FILE, 'w') as f:
            f.write('oauth2:' + access_token)
        self.api_client = client.DropboxClient(access_token)
        self.is_logged_in = True
    def logout(self):
        """log out of the current Dropbox account"""
        self.api_client = None
        os.unlink(self.TOKEN_FILE)
        self.current_path = ''
        self.is_logged_in = False

    def cat(self, path):
        """display the contents of a file"""
        f, metadata = self.api_client.get_file_and_metadata(self.current_path + "/" + path)
        self.stdout.write(f.read())
        self.stdout.write("\n")

    def mkdir(self, path):
        """create a new directory"""
        self.api_client.file_create_folder(self.current_path + "/" + path)

    def rm(self, path):
        """delete a file or directory"""
        self.api_client.file_delete(self.current_path + "/" + path)

    def mv(self, from_path, to_path):
        """move/rename a file or directory"""
        self.api_client.file_move(self.current_path + "/" + from_path,
                                  self.current_path + "/" + to_path)

    def share(self, path):
        print self.api_client.share(path)['url']

    def account_info(self):
        """display account information"""
        f = self.api_client.account_info()
        pprint.PrettyPrinter(indent=2).pprint(f)


    def get(self, from_path, to_path):
        """
        Copy file from Dropbox to local file and print out the metadata.

        Examples:
        Dropbox> get file.txt ~/dropbox-file.txt
        """
        to_file = open(os.path.expanduser(to_path), "wb")

        f, metadata = self.api_client.get_file_and_metadata(self.current_path + "/" + from_path)
        print 'Metadata:', metadata
        to_file.write(f.read())


    def thumbnail(self, from_path, to_path, size='large', format='JPEG'):
        """
        Copy an image file's thumbnail to a local file and print out the
        file's metadata.

        Examples:
        Dropbox> thumbnail file.txt ~/dropbox-file.txt medium PNG
        """
        to_file = open(os.path.expanduser(to_path), "wb")

        f, metadata = self.api_client.thumbnail_and_metadata(
                self.current_path + "/" + from_path, size, format)
        print 'Metadata:', metadata
        to_file.write(f.read())

    def put(self, from_path, to_path):
        """
        Copy local file to Dropbox

        Examples:
        Dropbox> put ~/test.txt dropbox-copy-test.txt
        """
        from_file = open(os.path.expanduser(from_path), "rb")

        return self.api_client.put_file(self.current_path + "/" + to_path, from_file)

    def search(self, string):
        """Search Dropbox for filenames containing the given string."""
        results = self.api_client.search(self.current_path, string)
        for r in results:
            self.stdout.write("%s\n" % r['path'])

    def help(self):
        # Find every "do_" attribute with a non-empty docstring and print
        # out the docstring.
        all_names = dir(self)
        cmd_names = []
        for name in all_names:
            if name[:3] == 'do_':
                cmd_names.append(name[3:])
        cmd_names.sort()
        for cmd_name in cmd_names:
            f = getattr(self, 'do_' + cmd_name)
            if f.__doc__:
                self.stdout.write('%s: %s\n' % (cmd_name, f.__doc__))

    # the following are for command line magic and aren't Dropbox-related
    def emptyline(self):
        pass

    def do_EOF(self, line):
        self.stdout.write('\n')
        return True

    def parseline(self, line):
        parts = shlex.split(line)
        if len(parts) == 0:
            return None, None, line
        else:
            return parts[0], parts[1:], line

