import os
import unittest

from rope.project import Project
from ropetest import testutils

class PythonFileRunnerTest(unittest.TestCase):

    def setUp(self):
        super(PythonFileRunnerTest, self).setUp()
        self.project_root = 'sample_project'
        testutils.remove_recursively(self.project_root)
        self.project = Project(self.project_root)
        self.pycore = self.project.get_pycore()

    def tearDown(self):
        testutils.remove_recursively(self.project_root)
        super(PythonFileRunnerTest, self).tearDown()

    def make_sample_python_file(self, file_path, get_text_function_source=None):
        self.project.get_root_folder().create_file(file_path)
        file = self.project.get_resource(file_path)
        if not get_text_function_source:
            get_text_function_source = "def get_text():\n    return 'run'\n\n"
        file_content = get_text_function_source + \
                       "output = open('output.txt', 'w')\noutput.write(get_text())\noutput.close()\n"
        file.write(file_content)
        
    def get_output_file_content(self, file_path):
        try:
            output_path = ''
            last_slash = file_path.rfind('/')
            if last_slash != -1:
                output_path = file_path[0:last_slash + 1]
            file = self.project.get_resource(output_path + 'output.txt')
            return file.read()
        except RopeException:
            return ''

    def test_making_runner(self):
        file_path = 'sample.py'
        self.make_sample_python_file(file_path)
        file_resource = self.project.get_resource(file_path)
        runner = self.pycore.run_module(file_resource)
        runner.wait_process()
        self.assertEquals('run', self.get_output_file_content(file_path))

    # FIXME: this does not work on windows
    def xxx_test_killing_runner(self):
        file_path = 'sample.py'
        self.make_sample_python_file(file_path,
                                     "def get_text():" +
                                     "\n    import time\n    time.sleep(1)\n    return 'run'\n")
        file_resource = self.project.get_resource(file_path)
        runner = self.pycore.run_module(file_resource)
        runner.kill_process()
        self.assertEquals('', self.get_output_file_content(file_path))

    def test_running_nested_files(self):
        self.project.get_root_folder().create_folder('src')
        file_path = 'src/sample.py'
        self.make_sample_python_file(file_path)
        file_resource = self.project.get_resource(file_path)
        runner = self.pycore.run_module(file_resource)
        runner.wait_process()
        self.assertEquals('run', self.get_output_file_content(file_path))

    def test_setting_process_input(self):
        file_path = 'sample.py'
        self.make_sample_python_file(file_path,
                                     "def get_text():" +
                                     "\n    import sys\n    return sys.stdin.readline()\n")
        temp_file_name = 'processtest.tmp'
        try:
            temp_file = open(temp_file_name, 'w')
            temp_file.write('input text\n')
            temp_file.close()
            file_resource = self.project.get_resource(file_path)
            stdin = open(temp_file_name)
            runner = self.pycore.run_module(file_resource, stdin=stdin)
            runner.wait_process()
            stdin.close()
            self.assertEquals('input text\n', self.get_output_file_content(file_path))
        finally:
            os.remove(temp_file_name)
        
    def test_setting_process_output(self):
        file_path = 'sample.py'
        self.make_sample_python_file(file_path,
                                     "def get_text():" +
                                     "\n    print 'output text'\n    return 'run'\n")
        temp_file_name = 'processtest.tmp'
        try:
            file_resource = self.project.get_resource(file_path)
            stdout = open(temp_file_name, 'w')
            runner = self.pycore.run_module(file_resource, stdout=stdout)
            runner.wait_process()
            stdout.close()
            temp_file = open(temp_file_name, 'r')
            self.assertEquals('output text\n', temp_file.read())
            temp_file.close()
        finally:
            os.remove(temp_file_name)

    def test_setting_pythonpath(self):
        src = self.project.get_root_folder().create_folder('src')
        src.create_file('sample.py')
        src.get_child('sample.py').write('def f():\n    pass\n')
        self.project.get_root_folder().create_folder('test')
        file_path = 'test/test.py'
        self.make_sample_python_file(file_path,
                                     "def get_text():" +
                                     "\n    import sample\n    sample.f()\n    return'run'\n")
        file_resource = self.project.get_resource(file_path)
        runner = self.pycore.run_module(file_resource)
        runner.wait_process()
        self.assertEquals('run', self.get_output_file_content(file_path))

def suite():
    result = unittest.TestSuite()
    result.addTests(unittest.makeSuite(PythonFileRunnerTest))
    return result

if __name__ == '__main__':
    unittest.main()