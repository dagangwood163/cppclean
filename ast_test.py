#!/usr/bin/env python
#
# Copyright 2008 Neal Norwitz
# Portions Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AST test."""

__author__ = 'nnorwitz@google.com (Neal Norwitz)'

import unittest

from cpp import ast
from cpp import tokenize


def _InstallGenericEqual(cls, attrs):
    """Add an __eq__ method to |cls| so objects can be compared for tests.

    Args:
      cls: Python class to add __eq__ method to
      attrs: string - space separated of attribute names to compare

    """
    attrs = attrs.split()

    def __eq__(self, other):
        if not isinstance(other, cls):
            return False
        for a in attrs:
            # Use not (a == other) since this could be recursive and
            # we don't define a not equals method.
            if not (getattr(self, a) == getattr(other, a)):
                return False
        return True
    cls.__eq__ = __eq__


def _InstallEqualMethods():
    """Install __eq__ methods on the appropriate objects used for testing."""
    _InstallGenericEqual(tokenize.Token, 'name')
    _InstallGenericEqual(ast.Class,
                         'name bases templated_types namespace body')
    _InstallGenericEqual(ast.Struct,
                         'name bases templated_types namespace body')
    _InstallGenericEqual(ast.Type, ('name templated_types modifiers '
                                    'reference pointer array'))
    _InstallGenericEqual(ast.Parameter, 'name type default')
    _InstallGenericEqual(ast.Function, ('name return_type parameters '
                                        'modifiers templated_types '
                                        'body namespace'))
    _InstallGenericEqual(ast.Method, ('name in_class return_type parameters '
                                      'modifiers templated_types '
                                      'body namespace'))
    _InstallGenericEqual(ast.Include, 'filename system')
_InstallEqualMethods()


def get_tokens(code_string):
    return tokenize.get_tokens(code_string + '\n')


def MakeBuilder(code_string):
    """Convenience function to make an AstBuilder from a code snippet.."""
    return ast.AstBuilder(get_tokens(code_string), '<test>')


def Token(name, start=0, end=0, token_type=tokenize.NAME):
    return tokenize.Token(token_type, name, start, end)


def Include(filename, system=False, start=0, end=0):
    return ast.Include(start, end, filename, system)


def Class(name, start=0, end=0, bases=None, body=None, templated_types=None,
          namespace=None):
    if namespace is None:
        namespace = []
    return ast.Class(start, end, name, bases, templated_types, body, namespace)


def Struct(name, start=0, end=0, bases=None, body=None, templated_types=None,
           namespace=None):
    if namespace is None:
        namespace = []
    return ast.Struct(start, end, name, bases, templated_types, body,
                      namespace)


def Type(name, start=0, end=0, templated_types=None, modifiers=None,
         reference=False, pointer=False, array=False):
    if templated_types is None:
        templated_types = []
    if modifiers is None:
        modifiers = []
    return ast.Type(start, end, name, templated_types, modifiers,
                    reference, pointer, array)


def Function(name, return_type, parameters, start=0, end=0,
             modifiers=0, templated_types=None, body=None, namespace=None):
    # TODO(nnorwitz): why are body & templated_types different
    # for Functions and Methods?
    if namespace is None:
        namespace = []
    return ast.Function(start, end, name, return_type, parameters,
                        modifiers, templated_types, body, namespace)


def Method(name, in_class, return_type, parameters, start=0, end=0,
           modifiers=0, templated_types=None, body=None, namespace=None):
    if templated_types is None:
        templated_types = []
    if body is None:
        body = []
    if namespace is None:
        namespace = []
    return ast.Method(start, end, name, in_class, return_type, parameters,
                      modifiers, templated_types, body, namespace)


class TypeConverter_declaration_to_partsTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testSimple(self):
        tokens = get_tokens('Fool data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual([], modifiers)

    def testSimpleModifiers(self):
        tokens = get_tokens('const volatile Fool data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual(['const', 'volatile'], modifiers)

    def testSimpleArray(self):
        tokens = get_tokens('Fool[] data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([], templated_types)
        self.assertEqual([], modifiers)

    def testSimpleTemplate(self):
        tokens = get_tokens('Fool<tt> data')
        name, type_name, templated_types, modifiers, default, other_tokens = \
            self.converter.declaration_to_parts(list(tokens), True)
        self.assertEqual('data', name)
        self.assertEqual('Fool', type_name)
        self.assertEqual([Type('tt')], templated_types)
        self.assertEqual([], modifiers)


class TypeConverter_to_parametersTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testReallySimple(self):
        tokens = get_tokens('int bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(False, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def testArray(self):
        tokens = get_tokens('int[] bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def testArrayPointerReference(self):
        params = 'const int[] bar, mutable char* foo, volatile Bar& babar'
        tokens = get_tokens(params)
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(3, len(results))

        self.assertEqual(['const'], results[0].type.modifiers)
        self.assertEqual('int', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

        self.assertEqual(['mutable'], results[1].type.modifiers)
        self.assertEqual('char', results[1].type.name)
        self.assertEqual([], results[1].type.templated_types)
        self.assertEqual(True, results[1].type.pointer)
        self.assertEqual(False, results[1].type.reference)
        self.assertEqual(False, results[1].type.array)
        self.assertEqual('foo', results[1].name)

        self.assertEqual(['volatile'], results[2].type.modifiers)
        self.assertEqual('Bar', results[2].type.name)
        self.assertEqual([], results[2].type.templated_types)
        self.assertEqual(False, results[2].type.pointer)
        self.assertEqual(True, results[2].type.reference)
        self.assertEqual(False, results[2].type.array)
        self.assertEqual('babar', results[2].name)

    def testArrayWithClass(self):
        tokens = get_tokens('Bar[] bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('Bar', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(True, results[0].type.array)
        self.assertEqual('bar', results[0].name)

    def testMultipleArgs(self):
        tokens = get_tokens('const volatile Fool* data, int bar, enum X foo')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(3, len(results))

        self.assertEqual(['const', 'volatile'], results[0].type.modifiers)
        self.assertEqual('Fool', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(True, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual('data', results[0].name)

        self.assertEqual([], results[1].type.modifiers)
        self.assertEqual('int', results[1].type.name)
        self.assertEqual([], results[1].type.templated_types)
        self.assertEqual(False, results[1].type.pointer)
        self.assertEqual(False, results[1].type.reference)
        self.assertEqual('bar', results[1].name)

        self.assertEqual(['enum'], results[2].type.modifiers)
        self.assertEqual('X', results[2].type.name)
        self.assertEqual([], results[2].type.templated_types)
        self.assertEqual(False, results[2].type.pointer)
        self.assertEqual(False, results[2].type.reference)
        self.assertEqual('foo', results[2].name)

    def testSimpleTemplateBegin(self):
        tokens = get_tokens('pair<int, int> data, int bar')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(2, len(results), repr(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('pair', results[0].type.name)
        self.assertEqual([Type('int'), Type('int')],
                         results[0].type.templated_types)
        self.assertEqual(False, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual('data', results[0].name)

        self.assertEqual([], results[1].type.modifiers)
        self.assertEqual('int', results[1].type.name)
        self.assertEqual([], results[1].type.templated_types)
        self.assertEqual(False, results[1].type.pointer)
        self.assertEqual(False, results[1].type.reference)
        self.assertEqual('bar', results[1].name)

    def testSimpleWithInitializers(self):
        tokens = get_tokens('Fool* data = NULL')
        results = self.converter.to_parameters(list(tokens))
        self.assertEqual(1, len(results))

        self.assertEqual([], results[0].type.modifiers)
        self.assertEqual('Fool', results[0].type.name)
        self.assertEqual([], results[0].type.templated_types)
        self.assertEqual(True, results[0].type.pointer)
        self.assertEqual(False, results[0].type.reference)
        self.assertEqual(False, results[0].type.array)
        self.assertEqual('data', results[0].name)
        self.assertEqual([Token('NULL')], results[0].default)


class TypeConverter_to_typeTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testSimple(self):
        tokens = get_tokens('Bar')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        self.assertEqual(Type('Bar'), result[0])

    def testTemplate(self):
        tokens = get_tokens('Bar<Foo>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        self.assertEqual(Type('Bar', templated_types=[Type('Foo')]),
                         result[0])

    def testTemplateWithMultipleArgs(self):
        tokens = get_tokens('Bar<Foo, Blah, Bling>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'), Type('Blah'), Type('Bling')]
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsStart(self):
        tokens = get_tokens('Bar<Foo<x>, Blah, Bling>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo', templated_types=[Type('x')]),
                 Type('Blah'),
                 Type('Bling')]
        self.assertEqual(types[0], result[0].templated_types[0])
        self.assertEqual(types[1], result[0].templated_types[1])
        self.assertEqual(types[2], result[0].templated_types[2])
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsMid(self):
        tokens = get_tokens('Bar<Foo, Blah<x>, Bling>')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'),
                 Type('Blah', templated_types=[Type('x')]),
                 Type('Bling')]
        self.assertEqual(Type('Bar', templated_types=types), result[0])

    def testTemplateWithMultipleTemplateArgsEnd(self):
        tokens = get_tokens('Bar<Foo, Blah, Bling<x> >')
        result = self.converter.to_type(list(tokens))
        self.assertEqual(1, len(result))
        types = [Type('Foo'),
                 Type('Blah'),
                 Type('Bling', templated_types=[Type('x')])]
        self.assertEqual(Type('Bar', templated_types=types), result[0])


class TypeConverter_create_return_typeTest(unittest.TestCase):

    def setUp(self):
        self.converter = ast.TypeConverter([])

    def testEmpty(self):
        self.assertEqual(None, self.converter.create_return_type(None))
        self.assertEqual(None, self.converter.create_return_type([]))

    def testSimple(self):
        tokens = get_tokens('Bar')
        result = self.converter.create_return_type(list(tokens))
        self.assertEqual(Type('Bar'), result)

    def testArray(self):
        tokens = get_tokens('Bar[]')
        result = self.converter.create_return_type(list(tokens))
        self.assertEqual(Type('Bar', array=True), result)

    def testConstPointer(self):
        tokens = get_tokens('const Bar*')
        result = self.converter.create_return_type(list(tokens))
        self.assertEqual(Type('Bar', modifiers=['const'], pointer=True),
                         result)

    def testConstClassPointer(self):
        tokens = get_tokens('const class Bar*')
        result = self.converter.create_return_type(list(tokens))
        modifiers = ['const', 'class']
        self.assertEqual(Type('Bar', modifiers=modifiers, pointer=True),
                         result)

    def testTemplate(self):
        tokens = get_tokens('const pair<int, NS::Foo>*')
        result = self.converter.create_return_type(list(tokens))
        templated_types = [Type('int'), Type('NS::Foo')]
        self.assertEqual(Type('pair', modifiers=['const'],
                              templated_types=templated_types, pointer=True),
                         result)


class AstBuilder_get_var_tokens_up_toTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_skip_if0blocksTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_get_matching_charTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilderget_nameTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_get_nested_typesTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_get_templated_typesTest(unittest.TestCase):

    def testSimple(self):
        builder = MakeBuilder('T> class')
        result = builder._get_templated_types()
        self.assertEqual(1, len(result))
        self.assertEqual((None, None), result['T'])

    def testMultiple(self):
        builder = MakeBuilder('T, U> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual((None, None), result['T'])
        self.assertEqual((None, None), result['U'])

    def testMultipleWithTypename(self):
        builder = MakeBuilder('typename T, typename U> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual((None, None), result['T'])
        self.assertEqual((None, None), result['U'])

    def testMultipleWithTypenameAndDefaults(self):
        builder = MakeBuilder('typename T=XX, typename U=YY> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual(None, result['T'][0])
        self.assertEqual(1, len(result['T'][1]))
        self.assertEqual('XX', result['T'][1][0].name)
        self.assertEqual(None, result['U'][0])
        self.assertEqual(1, len(result['U'][1]))
        self.assertEqual('YY', result['U'][1][0].name)

    def testMultipleWithUserDefinedTypeName(self):
        builder = MakeBuilder('class C, Type t> class')
        result = builder._get_templated_types()
        self.assertEqual(2, len(result))
        self.assertEqual((None, None), result['C'])
        self.assertEqual('Type', result['t'][0].name)


class AstBuilder_get_basesTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilder_get_classTest(unittest.TestCase):
    pass  # TODO(nnorwitz): implement.


class AstBuilderIntegrationTest(unittest.TestCase):

    """Unlike the other test cases in this file, this test case is meant to be
    an integration test.

    It doesn't test any individual
    method.  It tests whole code blocks.

    """

    # TODO(nnorwitz): add lots more tests.

    def testClass_ForwardDeclaration(self):
        nodes = list(MakeBuilder('class Foo;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', body=None), nodes[0])

    def testClass_EmptyBody(self):
        nodes = list(MakeBuilder('class Foo {};').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', body=[]), nodes[0])

    def testClass_InNamespaceSingle(self):
        nodes = list(MakeBuilder('namespace N { class Foo; }').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['N']), nodes[0])

    def testClass_InNamespaceMultiple(self):
        code = 'namespace A { namespace B { namespace C { class Foo; }}}'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', 'B', 'C']), nodes[0])

    def testClass_InNamespaceMultipleWithOneClosed(self):
        code = 'namespace A { namespace B {} namespace C { class Foo; }}'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', 'C']), nodes[0])

    def testClass_InAnonymousNamespaceSingle(self):
        nodes = list(MakeBuilder('namespace { class Foo; }').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=[None]), nodes[0])

    def testClass_InAnonymousNamespaceMultiple(self):
        code = 'namespace A { namespace { namespace B { class Foo; }}}'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=['A', None, 'B']), nodes[0])

    def testClass_NoAnonymousNamespace(self):
        nodes = list(MakeBuilder('class Foo;').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', namespace=[]), nodes[0])

    def testClass_VirtualInheritance(self):
        code = 'class Foo : public virtual Bar {};'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('Foo', bases=[Type('Bar')], body=[]), nodes[0])

    def testClass_VirtualInlineDestructor(self):
        code = 'class Foo { virtual inline ~Foo(); };'
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        function = nodes[0].body[0]
        expected = Function('Foo', [], [],
                            modifiers=ast.FUNCTION_DTOR | ast.FUNCTION_VIRTUAL)
        self.assertEqual(expected.return_type, function.return_type)
        self.assertEqual(expected, function)
        self.assertEqual(Class('Foo', body=[expected]), nodes[0])

    def testClass_ColonSeparatedClassNameAndInlineDtor(self):
        method_body = 'XXX(1) << "should work";'
        code = 'class Foo::Bar { ~Bar() { %s } };' % method_body
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        function = nodes[0].body[0]
        expected = Function('Bar', [], [], body=list(get_tokens(method_body)),
                            modifiers=ast.FUNCTION_DTOR)
        self.assertEqual(expected.return_type, function.return_type)
        self.assertEqual(expected, function)
        self.assertEqual(Class('Foo::Bar', body=[expected]), nodes[0])

    def testClass_HandlesStructRebind(self):
        code = """
        template <typename T, typename Alloc = std::allocator<T> >
        class AnotherAllocator : public Alloc {
            template <class U> struct rebind {
            };
        };
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Class('AnotherAllocator', bases=[Type('Alloc')],
                               body=[Struct('rebind', body=[])]),
                         nodes[0])
        # TODO(nnorwitz): assert more about the body of the class.

    def testFunction_ParsesOperatorBracket(self):
        code = """
        class A {
            const B& operator[](const int i) const {}
        };
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        function = nodes[0].body[0]
        expected = Function('operator[]', list(get_tokens('const B&')),
                            list(get_tokens('const int i')), body=[],
                            modifiers=ast.FUNCTION_CONST)
        self.assertEqual(expected.return_type, function.return_type)
        self.assertEqual(expected, function)
        self.assertEqual(Class('A', body=[expected]), nodes[0])

    def testFunction_ParsesTemplateWithArrayAccess(self):
        code = """
        template <typename T, size_t N>
        char (&ASH(T (&seq)[N]))[N];
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        # TODO(nnorwitz): this doesn't parse correctly, but at least
        # it doesn't raise an exception anymore.  Improve the parsing.

    def testMethod_WithTemplateClassWorks(self):
        code = """
        template <class T>
        inline void EVM::VH<T>::Write() {
        }
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        expected = Method('Write', list(get_tokens('EVM::VH<T>')),
                          list(get_tokens('inline void')), [],
                          templated_types={'T': (None, None)})
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def testMethod_WithTemplateClassWith2ArgsWorks(self):
        code = """
        template <class T, typename U>
        inline void EVM::VH<T, U>::Write() {
        }
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        expected = Method('Write', list(get_tokens('EVM::VH<T, U>')),
                          list(get_tokens('inline void')), [],
                          templated_types={'T': (None, None),
                                           'U': (None, None)})
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def testMethod_WithTemplateClassWith3ArgsWorks(self):
        code = """
        template <class CT, class IT, class DT>
        DT* Worker<CT, IT, DT>::Create() {
        }
        """
        nodes = list(MakeBuilder(code).generate())
        self.assertEqual(1, len(nodes))
        tt = (None, None)
        expected = Method('Create', list(get_tokens('Worker<CT, IT, DT>')),
                          list(get_tokens('DT*')), [],
                          templated_types={'CT': tt, 'IT': tt, 'DT': tt})
        self.assertEqual(expected.return_type, nodes[0].return_type)
        self.assertEqual(expected.in_class, nodes[0].in_class)
        self.assertEqual(expected.templated_types, nodes[0].templated_types)
        self.assertEqual(expected, nodes[0])

    def testInclude_WithBackslashContinuationWorks(self):
        nodes = list(MakeBuilder('#include \\\n  "test.h"').generate())
        self.assertEqual(1, len(nodes))
        self.assertEqual(Include('test.h'), nodes[0])


if __name__ == '__main__':
    unittest.main()