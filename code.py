from flask import Flask, request, jsonify
import subprocess
import tempfile
import os

app = Flask(__name__)

compilers = {
    'python': {
        'compile': 'python3 -m py_compile {source}',
        'run': 'python3 {source}'
    },
    'ruby': {
        'compile': 'ruby -c {source}',
        'run': 'ruby {source}'
    },
    'go': {
        'compile': 'go build -o {binary} {source}',
        'run': './{binary}'
    }
}

def compile_and_run(code, language):
    config = compilers.get(language)
    if not config:
        return {'error': f'Unsupported language: {language}'}

    with tempfile.TemporaryDirectory() as tmpdir:
        source_file = os.path.join(tmpdir, f'main.{language}')
        binary_file = os.path.join(tmpdir, 'main')
        with open(source_file, 'w') as f:
            f.write(code)

        compile_cmd = config['compile'].format(source=source_file, binary=binary_file)
        compile_proc = subprocess.run(compile_cmd, shell=True, capture_output=True, text=True)
        if compile_proc.returncode != 0:
            return {'error': compile_proc.stderr}

        run_cmd = config['run'].format(source=source_file, binary=binary_file)
        run_proc = subprocess.run(run_cmd, shell=True, capture_output=True, text=True)
        if run_proc.returncode != 0:
            return {'error': run_proc.stderr}

        return {'output': run_proc.stdout}

@app.route('/api/compile', methods=['POST'])
def api_compile():
    data = request.get_json()
    code = data.get('code')
    language = data.get('language')
    if not code or not language:
        return jsonify({'error': 'Code and language are required'}), 400
    result = compile_and_run(code, language)
    return jsonify(result)

def run_tests():
    test_cases = [
        {
            'language': 'python',
            'code': 'print("Hello, Python!")',
            'expected_output': 'Hello, Python!\n'
        },
        {
            'language': 'ruby',
            'code': 'puts "Hello, Ruby!"',
            'expected_output': "Hello, Ruby!\n"
        },
        {
            'language': 'go',
            'code': 'package main\nimport "fmt"\nfunc main() { fmt.Println("Hello, Go!") }',
            'expected_output': 'Hello, Go!\n'
        }
    ]

    for test in test_cases:
        result = compile_and_run(test['code'], test['language'])
        assert result['output'] == test['expected_output'], f"Test failed for {test['language']}: {result}"

if __name__ == '__main__':
    app.run(debug=True)
    run_tests()
