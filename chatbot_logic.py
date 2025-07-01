import re
from collections import Counter
import statistics
from flask import current_app
import subprocess
import os

# Global variables for chatbot data
analyzed_data = []
clustered_data = []

def set_analyzed_data(data):
    global analyzed_data
    analyzed_data = data

def get_analyzed_data():
    return analyzed_data

def analyze_data_for_chatbot():
    # Load analyzed data from file if it exists
    global analyzed_data
    if os.path.exists('analyzed_testcases.json'):
        import json
        with open('analyzed_testcases.json', 'r') as f:
            analyzed_data = json.load(f)
    if not analyzed_data:
        return {}
    analysis = {
        'total_failures': len(analyzed_data),
        'unique_commands': len(set(item['failing_command'] for item in analyzed_data)),
        'unique_tags': len(set(item['tag'] for item in analyzed_data)),
        'command_stats': Counter(item['failing_command'] for item in analyzed_data),
        'tag_stats': Counter(item['tag'] for item in analyzed_data),
        'most_common_command': None,
        'most_common_tag': None,
        'command_failure_rates': {},
        'tag_failure_rates': {},
        'error_patterns': {},
        'path_analysis': {},
        'severity_analysis': {},
        'command_tag_correlation': {},
        'failure_distribution': {}
    }
    if analysis['command_stats']:
        analysis['most_common_command'] = analysis['command_stats'].most_common(1)[0]
    if analysis['tag_stats']:
        analysis['most_common_tag'] = analysis['tag_stats'].most_common(1)[0]
    for item in analyzed_data:
        error_msg = item['error_message']
        if 'ERROR' in error_msg:
            if 'license' in error_msg.lower():
                analysis['error_patterns']['license_issues'] = analysis['error_patterns'].get('license_issues', 0) + 1
            if 'file' in error_msg.lower() and ('not found' in error_msg.lower() or 'cannot open' in error_msg.lower()):
                analysis['error_patterns']['file_not_found'] = analysis['error_patterns'].get('file_not_found', 0) + 1
            if 'parameter' in error_msg.lower():
                analysis['error_patterns']['parameter_issues'] = analysis['error_patterns'].get('parameter_issues', 0) + 1
            if 'build' in error_msg.lower():
                analysis['error_patterns']['build_issues'] = analysis['error_patterns'].get('build_issues', 0) + 1
            if 'test' in error_msg.lower():
                analysis['error_patterns']['test_issues'] = analysis['error_patterns'].get('test_issues', 0) + 1
    for item in analyzed_data:
        path = item['testcase_path']
        if 'customer' in path:
            analysis['path_analysis']['customer_tests'] = analysis['path_analysis'].get('customer_tests', 0) + 1
        if 'diagnostics' in path:
            analysis['path_analysis']['diagnostics_tests'] = analysis['path_analysis'].get('diagnostics_tests', 0) + 1
        if 'flow' in path:
            analysis['path_analysis']['flow_tests'] = analysis['path_analysis'].get('flow_tests', 0) + 1
        if 'eta' in path:
            analysis['path_analysis']['eta_tests'] = analysis['path_analysis'].get('eta_tests', 0) + 1
        if 'sanity' in path:
            analysis['path_analysis']['sanity_tests'] = analysis['path_analysis'].get('sanity_tests', 0) + 1
        if 'misc' in path:
            analysis['path_analysis']['misc_tests'] = analysis['path_analysis'].get('misc_tests', 0) + 1
    for item in analyzed_data:
        cmd = item['failing_command']
        tag = item['tag']
        if cmd not in analysis['command_tag_correlation']:
            analysis['command_tag_correlation'][cmd] = Counter()
        analysis['command_tag_correlation'][cmd][tag] += 1
    command_counts = list(analysis['command_stats'].values())
    if command_counts:
        analysis['failure_distribution'] = {
            'min_failures': min(command_counts),
            'max_failures': max(command_counts),
            'avg_failures': round(statistics.mean(command_counts), 2),
            'median_failures': statistics.median(command_counts),
            'commands_with_single_failure': sum(1 for count in command_counts if count == 1),
            'commands_with_multiple_failures': sum(1 for count in command_counts if count > 1)
        }
    return analysis

def process_chatbot_query(query):
    query = query.strip()
    # If query is a valid error tag or starts with msgHelp, run msgHelp
    error_tag_match = re.match(r'^(msghelp\s+)?([A-Z]{3,4}-\d+)$', query, re.IGNORECASE)
    if error_tag_match:
        tag = error_tag_match.group(2)
        try:
            result = subprocess.run(['msgHelp', tag], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            output = result.stdout.strip() or result.stderr.strip() or 'No output.'
            return f"[msgHelp {tag}]:\n{output}"
        except Exception as e:
            return f"Error running msgHelp: {e}"
    # ... fallback to normal analysis logic ...
    query_lower = query.lower().strip()
    analysis = analyze_data_for_chatbot()
    if not analysis:
        return "No data available for analysis."
    if any(word in query_lower for word in ['total', 'count', 'how many']):
        if 'failure' in query_lower or 'testcase' in query_lower:
            return f"📊 Total testcase failures: {analysis['total_failures']}"
        elif 'command' in query_lower:
            return f"📊 Total unique failing commands: {analysis['unique_commands']}"
        elif 'tag' in query_lower or 'error' in query_lower:
            return f"📊 Total unique error tags: {analysis['unique_tags']}"
    elif 'most common' in query_lower or 'frequent' in query_lower or 'fails most often' in query_lower:
        if 'command' in query_lower and analysis['most_common_command']:
            cmd, count = analysis['most_common_command']
            return f"🔍 Most common failing command: '{cmd}' with {count} failures"
        elif 'tag' in query_lower and analysis['most_common_tag']:
            tag, count = analysis['most_common_tag']
            return f"🔍 Most common error tag: '{tag}' with {count} occurrences"
    elif 'command' in query_lower and 'list' in query_lower:
        top_commands = analysis['command_stats'].most_common(5)
        result = "📋 Top 5 failing commands:\n"
        for i, (cmd, count) in enumerate(top_commands, 1):
            result += f"{i}. {cmd}: {count} failures\n"
        return result
    elif 'tag' in query_lower and 'list' in query_lower or 'most common error tags' in query_lower:
        top_tags = analysis['tag_stats'].most_common(5)
        result = "🏷️ Top 5 error tags:\n"
        for i, (tag, count) in enumerate(top_tags, 1):
            result += f"{i}. {tag}: {count} occurrences\n"
        return result
    elif 'pattern' in query_lower or 'type' in query_lower or 'error patterns in failures' in query_lower:
        if analysis['error_patterns']:
            result = "🔍 Common error patterns:\n"
            for pattern, count in analysis['error_patterns'].items():
                result += f"• {pattern.replace('_', ' ').title()}: {count} cases\n"
            return result
        else:
            return "No common error patterns identified."
    elif 'category' in query_lower or 'path' in query_lower or 'testcase categories have most failures' in query_lower:
        if analysis['path_analysis']:
            result = "📁 Testcase categories:\n"
            for category, count in analysis['path_analysis'].items():
                result += f"• {category.replace('_', ' ').title()}: {count} cases\n"
            return result
        else:
            return "No path analysis available."
    elif 'specific' in query_lower or 'find' in query_lower or 'failures for' in query_lower:
        for item in analyzed_data:
            if item['failing_command'].lower() in query_lower:
                return f"🔍 Command '{item['failing_command']}' has {analysis['command_stats'][item['failing_command']]} failures"
            if item['tag'].lower() in query_lower:
                return f"🔍 Tag '{item['tag']}' has {analysis['tag_stats'][item['tag']]} occurrences"
    elif 'help' in query_lower or 'what can' in query_lower:
        return (
            "You can ask me things like:\n"
            "• How many testcase failures are there?\n"
            "• Which command fails most often?\n"
            "• What are the most common error tags?\n"
            "• Show error patterns in failures\n"
            "• Which testcase categories have most failures?\n"
            "• Show failure statistics\n"
            "• What should I fix first?\n"
            "Or just enter an error tag (like TTM-004) to get help for that error."
        )
    elif 'statistics' in query_lower or 'stats' in query_lower or 'failure statistics' in query_lower:
        result = f"""📊 Testcase Failure Statistics:\n• Total failures: {analysis['total_failures']}\n• Unique commands: {analysis['unique_commands']}\n• Unique error tags: {analysis['unique_tags']}\n• Most common command: {analysis['most_common_command'][0] if analysis['most_common_command'] else 'N/A'} ({analysis['most_common_command'][1] if analysis['most_common_command'] else 0} failures)\n• Most common tag: {analysis['most_common_tag'][0] if analysis['most_common_tag'] else 'N/A'} ({analysis['most_common_tag'][1] if analysis['most_common_tag'] else 0} occurrences)"""
        if analysis.get('failure_distribution'):
            dist = analysis['failure_distribution']
            result += f"""\n📈 Failure Distribution:\n• Min failures per command: {dist['min_failures']}\n• Max failures per command: {dist['max_failures']}\n• Average failures per command: {dist['avg_failures']}\n• Median failures per command: {dist['median_failures']}\n• Commands with single failure: {dist['commands_with_single_failure']}\n• Commands with multiple failures: {dist['commands_with_multiple_failures']}"""
        return result
    elif 'distribution' in query_lower or 'failure distribution' in query_lower:
        if analysis.get('failure_distribution'):
            dist = analysis['failure_distribution']
            return f"""📈 Failure Distribution Analysis:\n• Minimum failures per command: {dist['min_failures']}\n• Maximum failures per command: {dist['max_failures']}\n• Average failures per command: {dist['avg_failures']}\n• Median failures per command: {dist['median_failures']}\n• Commands with single failure: {dist['commands_with_single_failure']}\n• Commands with multiple failures: {dist['commands_with_multiple_failures']}"""
        else:
            return "No distribution data available."
    elif 'correlation' in query_lower or 'command tag' in query_lower:
        if analysis.get('command_tag_correlation'):
            result = "🔗 Command-Tag Correlations:\n"
            for cmd, tag_counts in list(analysis['command_tag_correlation'].items())[:5]:
                result += f"• {cmd}:\n"
                for tag, count in tag_counts.most_common(3):
                    result += f"  - {tag}: {count} times\n"
            return result
        else:
            return "No correlation data available."
    elif 'export' in query_lower or 'download' in query_lower:
        return "💾 Export Options:\n• Use the export button in the main table\n• Data can be exported as CSV\n• Chatbot analysis can be copied from responses"
    elif 'recommend' in query_lower or 'suggestion' in query_lower or 'priority' in query_lower or 'fix first' in query_lower:
        if analysis.get('most_common_command') and analysis.get('most_common_tag'):
            cmd, cmd_count = analysis['most_common_command']
            tag, tag_count = analysis['most_common_tag']
            return f"""🎯 Priority Recommendations:\n• Focus on command '{cmd}' (most failures: {cmd_count})\n• Address error tag '{tag}' (most occurrences: {tag_count})\n• Check for common error patterns in the data\n• Review testcase categories with highest failure rates"""
        else:
            return "No recommendations available without data analysis."
    else:
        return "I'm not sure how to answer that. Try asking about total failures, most common commands/tags, error patterns, or type 'help' for more options." 