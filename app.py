#!/usr/bin/env python3

import os
import re
import subprocess
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from collections import defaultdict, Counter
import statistics
from chatbot_logic import analyze_data_for_chatbot, process_chatbot_query

app = Flask(__name__)
CORS(app)

def read_testcases(file_path='testcases.txt'):
    try:
        with open(file_path) as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("❌ ERROR: testcases.txt not found.")
        return []

def get_status_log_failing_command(tc_path):
    status_file = os.path.join(tc_path, "status.log")
    if not os.path.exists(status_file):
        return None
    with open(status_file) as f:
        for line in f:
            m = re.match(r".*EXIT STATUS for (\w+) is 5", line)
            if m:
                return m.group(1)
    return None

def get_make_n_failing_order(tc_path, available_diff_files):
    try:
        result = subprocess.run(['make', '-n'], cwd=tc_path,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        for line in result.stdout.splitlines():
            if 'testresults/logs' in line and '>' in line:
                log_file = line.split('>')[-1].strip().split('/')[-1]
                base = re.sub(r'\.log$', '', re.sub(r'^log_', '', log_file, flags=re.I), flags=re.I)
                if f"{base}.diff.bak" in available_diff_files:
                    return base
    except Exception:
        pass
    return None

def extract_first_error_line(diff_file_path):
    try:
        with open(diff_file_path) as f:
            for line in f:
                if line.strip().startswith('>') and "ERROR" in line:
                    return line.strip()
    except Exception:
        return None
    return None

def extract_error_tag(error_line):
    if not error_line:
        return None
    m = re.search(r'\(([A-Z]{3,4}-\d+)\)', error_line)
    return m.group(1) if m else None

def analyze_testcases(testcases):
    rows = []

    for tc in testcases:
        if not os.path.isdir(tc):
            continue

        status_cmd = get_status_log_failing_command(tc)
        diff_files = [f for f in os.listdir(tc) if f.endswith(".diff.bak")]
        make_cmd = get_make_n_failing_order(tc, diff_files)
        final_cmd = status_cmd or make_cmd

        if final_cmd:
            diff_file_path = os.path.join(tc, f"{final_cmd}.diff.bak")
            error_line = extract_first_error_line(diff_file_path)

            if error_line:
                tag = extract_error_tag(error_line)
                if not tag:
                    continue  # Only include testcases with issue

                short_error = (
                    error_line if len(error_line) <= 45 else error_line[:42] + "..."
                )
                rows.append([tc, final_cmd, short_error, tag])

    return rows

def get_clustered_data():
    """Return clustered data for the summary table (REAL data from testcases.txt and error lists)"""
    # Read real testcases
    testcase_file = os.path.join('scripts', 'result_reg', 'testcases.txt')
    testcases = read_testcases(testcase_file)
    data = analyze_testcases(testcases)
    clusters = {}
    for row in data:
        tc_path, cmd, err, tag = row
        if cmd not in clusters:
            clusters[cmd] = {}
        if tag not in clusters[cmd]:
            clusters[cmd][tag] = {'error_message': err, 'testcases': []}
        clusters[cmd][tag]['testcases'].append(tc_path)
    # Prepare summary for frontend
    summary = []
    for cmd, tag_dict in clusters.items():
        unique = len(tag_dict)
        total = sum(len(v['testcases']) for v in tag_dict.values())
        summary.append({
            'failing_command': cmd,
            'unique_failures': unique,
            'total_failures': total,
            'tags': [
                {
                    'tag': tag,
                    'error_message': tag_dict[tag]['error_message'],
                    'count': len(tag_dict[tag]['testcases'])
                } for tag in tag_dict
            ]
        })
    # Sort by total_failures in descending order
    summary.sort(key=lambda x: x['total_failures'], reverse=True)
    # Add S.No after sorting
    for i, item in enumerate(summary, 1):
        item['sno'] = i
    return summary, clusters

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/testcases')
def get_testcases():
    """API endpoint to get testcase data (REAL data from testcases.txt)"""
    try:
        testcase_file = os.path.join('scripts', 'result_reg', 'testcases.txt')
        testcases = read_testcases(testcase_file)
        data = []
        rows = analyze_testcases(testcases)
        for row in rows:
            data.append({
                "testcase_path": row[0],
                "failing_command": row[1],
                "error_message": row[2],
                "tag": row[3]
            })
        # Update global data for chatbot
        global analyzed_data, clustered_data
        analyzed_data = data
        clustered_data, _ = get_clustered_data()
        # Save analyzed data to file for chatbot
        with open('analyzed_testcases.json', 'w') as f:
            json.dump(data, f, indent=2)
        return jsonify({
            "total_cases": len(testcases),
            "filtered_cases": len(data),
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "testcases": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint to run the actual analysis"""
    try:
        testcases = read_testcases()
        if not testcases:
            return jsonify({"error": "No testcases found"}), 404
        
        rows = analyze_testcases(testcases)
        data = []
        for row in rows:
            data.append({
                "testcase_path": row[0],
                "failing_command": row[1],
                "error_message": row[2],
                "tag": row[3]
            })
        
        # Update global data for chatbot
        global analyzed_data
        analyzed_data = data
        
        return jsonify({
            "total_cases": len(testcases),
            "filtered_cases": len(data),
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "testcases": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clustered')
def api_clustered():
    summary, clusters = get_clustered_data()
    return jsonify({'summary': summary})

@app.route('/api/clustered/details')
def api_clustered_details():
    cmd = request.args.get('command')
    tag = request.args.get('tag')
    _, clusters = get_clustered_data()
    if cmd in clusters and tag in clusters[cmd]:
        return jsonify({
            'command': cmd,
            'tag': tag,
            'error_message': clusters[cmd][tag]['error_message'],
            'testcases': clusters[cmd][tag]['testcases']
        })
    return jsonify({'error': 'Not found'}), 404

@app.route('/testcases')
def testcase_paths_page():
    cmd = request.args.get('command')
    tag = request.args.get('tag')
    _, clusters = get_clustered_data()
    testcase_paths = []
    error_message = ''
    if cmd in clusters and tag in clusters[cmd]:
        testcase_paths = clusters[cmd][tag]['testcases']
        error_message = clusters[cmd][tag]['error_message']
    return render_template('testcase_paths.html', command=cmd, tag=tag, error_message=error_message, testcase_paths=testcase_paths)

@app.route('/api/msghelp', methods=['POST'])
def api_msghelp():
    data = request.get_json()
    error_id = data.get('error_id', '').strip()
    # Only allow safe error IDs like TTM-004
    if not re.match(r'^[A-Z]{3,4}-\d+$', error_id):
        return jsonify({'error': 'Invalid error ID format.'}), 400
    try:
        result = subprocess.run(['msgHelp', error_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        output = result.stdout.strip() or result.stderr.strip() or 'No output.'
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    """Advanced chatbot endpoint for data analysis queries"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Process the query using our AI analysis
        response = process_chatbot_query(query)
        
        return jsonify({
            'response': response,
            'query': query,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/suggestions')
def api_chatbot_suggestions():
    """Get suggested questions for the chatbot"""
    suggestions = [
        "How many total failures?",
        "What's the most common command?",
        "List top failing commands",
        "Show error patterns",
        "What are the testcase categories?",
        "Show statistics",
        "Find specific command migrate_pdl_tests",
        "Find specific tag TTM-004"
    ]
    return jsonify({'suggestions': suggestions})

@app.route('/api/chatbot/data')
def api_chatbot_data():
    """Get current data summary for chatbot"""
    try:
        analysis = analyze_data_for_chatbot()
        data_available = bool(analysis and analysis.get('total_failures', 0) > 0)
        total_records = analysis.get('total_failures', 0) if analysis else 0
        return jsonify({
            'analysis': analysis,
            'data_available': data_available,
            'total_records': total_records
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/export', methods=['POST'])
def api_chatbot_export():
    """Export chatbot analysis as JSON"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        response = data.get('response', '')
        
        # Create export data
        export_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'query': query,
            'response': response,
            'analysis_summary': analyze_data_for_chatbot()
        }
        
        return jsonify({
            'export_data': export_data,
            'filename': f'chatbot_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/error_table')
def error_table():
    """API endpoint to get the enhanced error summary table by Failing Command"""
    import json
    base_dir = os.path.join('scripts', 'result_reg')
    def read_list(filename):
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            return set()
        with open(path) as f:
            return set(line.strip() for line in f if line.strip())
    # Read error lists
    core = read_list('list_core')
    nc_diff = read_list('list_nc_diff')
    simulate_diff = read_list('list_simulate_diff')
    # Get clustered data (by Failing Command)
    summary, clusters = get_clustered_data()
    rows = []
    s_no = 1
    for item in summary:
        cmd = item['failing_command']
        # All testcases for this command
        all_tcs = []
        for taginfo in item['tags']:
            tag = taginfo['tag']
            if cmd in clusters and tag in clusters[cmd]:
                all_tcs.extend(clusters[cmd][tag]['testcases'])
        all_tcs = set(all_tcs)
        # Testcases in each error file
        core_tcs = list(all_tcs & core)
        nc_diff_tcs = list(all_tcs & nc_diff)
        simulate_diff_tcs = list(all_tcs & simulate_diff)
        others_tcs = [tc for tc in all_tcs if tc not in core and tc not in nc_diff and tc not in simulate_diff]
        # Count in each error file
        core_count = len(core_tcs)
        nc_diff_count = len(nc_diff_tcs)
        simulate_diff_count = len(simulate_diff_tcs)
        others_count = len(others_tcs)
        row = {
            'sno': s_no,
            'failing_command': cmd,
            'core_error': core_count,
            'core_error_testcases': core_tcs[:3],
            'nc_diff_error': nc_diff_count,
            'nc_diff_error_testcases': nc_diff_tcs[:3],
            'simulate_diff_error': simulate_diff_count,
            'simulate_diff_error_testcases': simulate_diff_tcs[:3],
            'make_error': '',
            'others': others_count,
            'others_error_testcases': others_tcs[:3]
        }
        rows.append(row)
        s_no += 1
    return jsonify({'table': rows})

@app.route('/error_testcases')
def error_testcases():
    """Return testcase paths for a given command and error type (and tag if provided)"""
    command = request.args.get('command')
    error_type = request.args.get('error_type')
    tag = request.args.get('tag')
    import os
    base_dir = os.path.join('scripts', 'result_reg')
    def read_list(filename):
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            return set()
        with open(path) as f:
            return set(line.strip() for line in f if line.strip())
    core = read_list('list_core')
    nc_diff = read_list('list_nc_diff')
    simulate_diff = read_list('list_simulate_diff')
    summary, clusters = get_clustered_data()
    testcases = set()
    if command in clusters:
        if error_type == 'tag' and tag:
            if tag in clusters[command]:
                testcases = set(clusters[command][tag]['testcases'])
        else:
            for t in clusters[command]:
                tcs = set(clusters[command][t]['testcases'])
                if error_type == 'core':
                    testcases |= (tcs & core)
                elif error_type == 'nc_diff':
                    testcases |= (tcs & nc_diff)
                elif error_type == 'simulate_diff':
                    testcases |= (tcs & simulate_diff)
                elif error_type == 'others':
                    testcases |= (tcs - core - nc_diff - simulate_diff)
                elif error_type == 'all':
                    testcases |= tcs
    return jsonify({'testcases': sorted(testcases)})

@app.route('/error_testcases_page')
def error_testcases_page():
    return render_template('error_testcases_page.html')

@app.route('/api/combined_table')
def combined_table():
    """API endpoint for the combined summary table by Failing Command"""
    import os
    base_dir = os.path.join('scripts', 'result_reg')
    def read_list(filename):
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            return set()
        with open(path) as f:
            return set(line.strip() for line in f if line.strip())
    core = read_list('list_core')
    nc_diff = read_list('list_nc_diff')
    simulate_diff = read_list('list_simulate_diff')
    # Get clustered data (by Failing Command)
    summary, clusters = get_clustered_data()
    rows = []
    s_no = 1
    for item in summary:
        cmd = item['failing_command']
        # All testcases and tags for this command
        all_tcs = []
        tag_counts = {}
        for taginfo in item['tags']:
            tag = taginfo['tag']
            tag_count = 0
            if cmd in clusters and tag in clusters[cmd]:
                tcs = clusters[cmd][tag]['testcases']
                all_tcs.extend(tcs)
                tag_count = len(tcs)
            tag_counts[tag] = tag_count
        all_tcs = set(all_tcs)
        # Error type counts
        core_count = len(all_tcs & core)
        nc_diff_count = len(all_tcs & nc_diff)
        simulate_diff_count = len(all_tcs & simulate_diff)
        others_count = len([tc for tc in all_tcs if tc not in core and tc not in nc_diff and tc not in simulate_diff])
        # Top tags (by count)
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_tags = [{'tag': t, 'count': c} for t, c in top_tags if c > 0]
        row = {
            'sno': s_no,
            'failing_command': cmd,
            'total_failures': len(all_tcs),
            'unique_tags': len(tag_counts),
            'core_error': core_count,
            'nc_diff_error': nc_diff_count,
            'simulate_diff_error': simulate_diff_count,
            'make_error': '',
            'others': others_count,
            'top_tags': top_tags
        }
        rows.append(row)
        s_no += 1
    return jsonify({'table': rows})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 