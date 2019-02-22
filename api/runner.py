"""
Test runner for python, see runner_spec for example usage
"""

import traceback

COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_RESET = "\033[0m"

def describe(description, outer=None):
    """
    Initilizes a new test group object using Describe

    Accepts:
    - description (STRING)          a string describing the test group
    - [outer] (Describe instance)   another test group to inherit common state from, optional

    Returns:
    - An instance of Describe
    """

    return Describe(description, outer)

class Describe:
    """
    A class to describe a new test group

    On initialization, accepts:
    - description (STRING)          see above
    - [outer] (Describe instance)   see above, optional

    Returns: An instance of Describe with the following attributes & methods, plus those above:
    - tests                 (LIST)      an empty list where each test function will be stored
    - inners                (LIST)      an empty list where any nested test groups will be stored
    - base, tab, & tabplus  (STRING)    strings used to increment tabs for results printing
    - it                    (METHOD)    a method used to create a new test in the group,
                                        adds an instance of Test to the self.tests list
    - [outer]               (Describe)  the outer test group, if nested, optional
    - [run]                 (FUNCTION)  a method used to run the test group & any inners,
                                        this one will only exist if it has no outer attribute

    This class has a modified __get_attr__() method used to inherit attributes & methods
    from the Describe object designated at self.outer (if there is one). It is used similarly
    to Ruby's method_missing.
    """

    def __init__(self, description, outer=None):
        self.description = description
        self.tests = []
        self.inners = []
        self.base = ''
        self.tab = '  '
        self.tabplus = self.tab + '  '

        if outer is not None:
            self.outer = outer
            self.base = self.tab
            self.tab += '  '
            outer.inners.append(self)
        else:
            self.run = self._run

    # A short name is chosen as the method will be referenced very often by the
    # end user of this test runner; the pylint warning about name snake case
    # has been disabled.
    def it(self, description, code): # pylint: disable=invalid-name
        """
        A method used to create a new test in the group, adds an instance of Test to
        the self.tests list.
        """

        test_obj = Test(description, code)
        self.tests.append(test_obj)

        return test_obj

    def _run(self):
        """
        a method used to run the test group & any inners,
        this one will only exist if it has no outer attribute
        """

        print(f'{self.base}{self.description}')

        if self.inners is not None:
            for inner in self.inners:
                # call to inner's protected run() method first to display any nested
                # test group's results before displaying the outer class results last
                inner._run() # pylint: disable=protected-access

        for test in self.tests:
            print(f'{self.tab}- {test.name}', end='')

            if test.success:
                print(f': {COLOR_GREEN}ok{COLOR_RESET}')
            else:
                print(f': {COLOR_RED}fail{COLOR_RESET}')

                print(f'{self.tabplus}{COLOR_RED}* STACK TRACE{COLOR_RESET}')

                for line in test.tb[:-1]:
                    print(f'{self.tabplus}{COLOR_RED}|{COLOR_RESET} {line}')

                print(f'{self.tabplus}{COLOR_RED}* {test.tb[-1]}{COLOR_RESET}')

    def __getattr__(self, method_name):
        def doesnt_exist():
            raise AttributeError(f'No such attribute: {method_name}')

        if method_name in ('run', 'outer'):
        # if method_name == 'run' or method_name == 'outer':
            return doesnt_exist()

        for key in dir(self.outer):
            if key == method_name:
                return getattr(self.outer, key)

        return doesnt_exist()

class Test:
    """
    An object used to represent a single test.

    On initialization, it takes:
    - name      (STRING)        a name to print when running the test,
                                should be descriptive, readable, & concise
    - code      (FUNCTION)      a function to be run when the test is executed,
                                the code must return a result to be handled by one
                                of the methods given by Should
                (EXPRESSION)    alternatively, code can be a non-callable value

    A test object also has the following attribute:
    - success   (BOOL)          represents if the test is successful or not,
                                value is set methods on Should

    A Test object also contains a Should object that makes Assertations &
    determines if the test passes or fails
    """

    def __init__(self, name, code):
        self.name = name
        self.code = code
        self.should = self._init_should()

    def _init_should(self):
        return self.Should(self.code, self)

    class Should:
        """
        An object containing methods for making Assertations of different types.
        An inner class to Test & always initialized when a Test instance is initialized.

        On initialization, it takes:
        - code          (FUNCTION)      a function that evaluates to an Actual result, to be
                                        compared against the Expected result using one of the
                                        methods of Should
                        (EXPRESSION)    alternatively, code can be a non-callable value
        - test_called   (Test)          the instance of Test that initialized this instance
                                        of Should

        Contains the following methods:
        - eq            compares the result of code to a given value, modifies test.success
                        accordingly, & returns the newly modified Test object
        - raise_error   compares the code result to an expected Exception class,
                        otherwise the same as eq
        """

        def __init__(self, code, test_called):
            self.code = code
            self.test_called = test_called

        def _code_result(self):
            return self.code() if callable(self.code) else self.code

        # A short name is chosen as the method will be referenced very often by the
        # end user of this test runner; the pylint warning about name snake case
        # has been disabled.
        def eq(self, expected): # pylint: disable=invalid-name
            """
            Compares _code_result() to expected, modifies the outer Test instance's
            success attribute accordingly, & returns the newly modified Test instance
            """

            try:
                code_result = self._code_result()

                if not code_result == expected:
                    raise AssertionError(f'expected {expected}, but got {code_result}')

                self.test_called.success = True

            # All exceptions are caught in order to continue parsing other tests.
            # Caught exceptions are stored at the Test instance's `err` & `tb`
            # attributes & will be displayed in the test failure message
            except Exception as err: # pylint: disable=broad-except
                self.test_called.success = False
                self.test_called.err = err
                self.test_called.tb = traceback.format_exc().splitlines()

            return self.test_called

        def raise_error(self, expected_err):
            """
            Compares _code_result() to expected_err, modifies the outer Test instance's
            success attribute accordingly, & returns the newly modified Test instance
            """

            try:
                code_result = self._code_result()

                self.test_called.success = False
                no_err_msg = f'No error was raised, instead got {code_result}'
                self.test_called.err = no_err_msg
                self.test_called.tb = [no_err_msg]

            # All exceptions are caught in order to continue parsing other tests.
            # Caught exceptions are stored at the Test instance's `err` & `tb`
            # attributes & will be displayed in the test failure message
            except Exception as err: # pylint: disable=broad-except
                # disabling pylint warning on typecheck as the only test that should
                # pass is if the exact specified error is passed, not any children of
                # the exception class
                if not type(err) == expected_err: # pylint: disable=unidiomatic-typecheck
                    # AssertionErrors are re-raised if the type of error does not match
                    # the expected error class, these will be caught in the next block
                    raise AssertionError(f'expected {expected_err}, but got {err}')

                self.test_called.success = True

            # Assertion Errors are caught after the general `except Exception` clause
            # as the Assertion error should be raised by the previous, more general clause
            except AssertionError as err: # pylint: disable=bad-except-order
                self.test_called.success = False
                self.test_called.err = err
                self.test_called.tb = traceback.format_exc().splitlines()

            return self.test_called