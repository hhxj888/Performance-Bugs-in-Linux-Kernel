from typing import List
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import re
import os
import logging

app = Flask(__name__)
app.secret_key = 'xxxxxx'

with open('./data_perf_final.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

data_size = len(data)

# ========== Multi-annotator configuration ==========
USERS = {
    'annotator1': 'pass1',
    'annotator2': 'pass2',
}

# Per-user current index (in-memory cache; file is the source of truth)
user_current_index = {}

def get_username():
    """Get current logged-in username from session."""
    return session.get('username', None)

def get_user_index_file(username):
    """Get the progress file path for a specific user."""
    return f'./view_perf_info_{username}'

def get_user_perf_path(username):
    return f'./data_perf_final_{username}.json'

def get_user_no_perf_path(username):
    return f'./data_no_perf_final_{username}.json'

error_commit_info = {
    "index": -1,
    "processed_commit": "ERROR",
    "record": {
        "bug_commit_hash": ["ERROR"],
        "commit": "ERROR",
        "fix_commit_hash": "ERROR",
        "id": "ERROR",
        "language": ["c"],
        "repo_name": "torvalds/linux"
    }
}

def process_commit(commit_text):
    """Extract commit message (text between Date line and diff)."""
    date_pattern = r'Date:\s+(\w{3} \w{3} \d{1,2} \d{2}:\d{2}:\d{2} \d{4} [+-]\d{4})'
    start_pattern = re.search(date_pattern, commit_text)
    if start_pattern:
        start_index = start_pattern.end() + 1
        end_index = commit_text.find("diff --git")
        extracted_text = commit_text[start_index:end_index].strip()
        return extracted_text
    else:
        return "Date pattern not found in the commit text."

def extract_git_diff(commit_text):
    """Extract the git diff portion from the full commit text."""
    diff_start = commit_text.find("diff --git")
    if diff_start != -1:
        return commit_text[diff_start:].strip()
    else:
        return "No git diff found in the commit text."

def get_file_info_in_commit(commit_text):
    """Extract the filename from the first diff header."""
    pattern = r'diff --git a/(.*?) b/'
    result = re.search(pattern, commit_text)
    if result:
        return result.group(1)
    else:
        return "No matching file found"

performance_phrases = [
    "performance regression",
    "regression in performance",
    "degradation",
    "laggy",
    "decline in performance",
    "lower performance",
    "worse performance",
    "worsening performance",
    "bad performance",
    "deterioration",
    "performance bug",
    "poor performance",
    "latency",
    "slowdown",
    "slower",
    "slow",
    "throughput",
    "hit in performance",
    "performance hit",
    "drop in performance",
    "performance drop",
    "worsen performance",
    "worsened performance",
    "memory issue",
    "memory usage",
    "gpu usage",
    "cpu usage",
    "response time",
]

def red_text(commit_info):
    """Highlight performance-related phrases in red."""
    for word in performance_phrases:
        if re.search(r'\b' + word + r'\b', commit_info):
            commit_info = commit_info.replace(word, f'<span class="red-text">{word}</span>')
    return commit_info

def save_category_info(new_category: List):
    """Save category info to file, deduplicating with existing entries."""
    try:
        category_set = read_category_info()
        for cate in new_category:
            category_set.add(cate.lower())
        with open('./category_list', 'w') as f:
            for category in category_set:
                f.write(category + '\n')
    except FileNotFoundError:
        with open('./category_list', 'w') as f:
            for cate in new_category:
                f.write(cate + '\n')

def read_category_info():
    """Read category set from file."""
    category_set = set()
    with open('./category_list', 'r') as f:
        for line in f:
            if line == '\n':
                continue
            category_set.add(line[:-1])
    return category_set


@app.route('/')
def init():
    return redirect('/loginPage/')

@app.route('/loginPage/')
def loginPage():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in USERS and USERS[username] == password:
        session['logged_in'] = True
        session['username'] = username
        idx_file = get_user_index_file(username)
        if not os.path.exists(idx_file):
            with open(idx_file, 'w') as f:
                f.write('0\n' + str(data[0]['id']))
        return redirect(url_for('main'))
    else:
        return render_template('login.html', error='Invalid username or password')

@app.route('/main')
def main():
    if 'logged_in' in session and session['logged_in']:
        username = get_username()
        return render_template('index_show_perf_detail_gui.html', username=username)
    else:
        return redirect('/loginPage/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/loginPage/')

@app.route("/get_index")
def get_index():
    username = get_username()
    index, id = read_index_info(username)
    return jsonify({'id': id, 'index': index})

def get_current_commit(index, username):
    """Fetch and return the commit at the given index for the user."""
    app.logger.debug("Current index: " + str(index) + " user: " + username)
    global data
    index = int(index)
    record = data[index]
    save_index_info(index, record['id'], username)
    processed_commit = process_commit(record['commit'])
    git_diff = extract_git_diff(record['commit'])
    file_info = get_file_info_in_commit(record['commit'])
    commit_info = red_text(record['commit'])
    record['commit'] = commit_info
    return jsonify({
        'record': record,
        'processed_commit': processed_commit,
        'git_diff': git_diff,
        'index': index,
        'code': file_info
    })

@app.route('/prev_record/', methods=['GET'])
def get_prev_commit():
    username = get_username()
    current_index = user_current_index.get(username, 0)
    if current_index <= 0:
        current_index = -1
        user_current_index[username] = current_index
        info = 'This is already the first message'
        error_commit_info['processed_commit'] = info
        return jsonify(error_commit_info)
    else:
        current_index -= 1
        user_current_index[username] = current_index
        return get_current_commit(current_index, username)

@app.route('/next_record/', methods=['GET'])
def get_next_commit():
    username = get_username()
    current_index = user_current_index.get(username, 0)
    global data_size
    if current_index >= data_size - 1:
        current_index = data_size
        user_current_index[username] = current_index
        info = 'This is already the last message'
        error_commit_info['processed_commit'] = info
        return jsonify(error_commit_info)
    else:
        current_index += 1
        user_current_index[username] = current_index
        return get_current_commit(current_index, username)

@app.route('/init_record/', methods=['GET'])
def get_init_record():
    username = get_username()
    index, id = read_index_info(username)
    current_index = int(index)
    user_current_index[username] = current_index
    return get_current_commit(index, username)

def save_index_info(index, id, username):
    """Save current progress index for a specific user."""
    strs = str(index) + '\n' + str(id)
    idx_file = get_user_index_file(username)
    with open(idx_file, 'w') as f:
        f.write(strs)

def read_index_info(username):
    """Read current progress index for a specific user."""
    idx_file = get_user_index_file(username)
    if not os.path.exists(idx_file):
        return '0', str(data[0]['id'])
    with open(idx_file, 'r') as f:
        content = f.read()
    index, id = content.split('\n')
    return index, id

@app.route('/latest_record/', methods=['GET'])
def get_last_record():
    username = get_username()
    index, id = read_index_info(username)
    return jsonify({'id': id, 'index': index})

@app.route('/get_category/', methods=['GET'])
def get_category():
    category_set = read_category_info()
    return jsonify({'category': list(category_set)})

@app.route('/save_json/', methods=['POST'])
def save_commit_info():
    """Save annotation result (category + reason + is_perf) for current commit."""
    username = get_username()
    perf_commit_path = get_user_perf_path(username)
    no_perf_commit_path = get_user_no_perf_path(username)
    if request.is_json:
        json_data = request.json
        global data
        current_index = user_current_index.get(username, 0)
        if json_data['is_perf']:
            file_path = perf_commit_path
        else:
            file_path = no_perf_commit_path
        index = current_index
        new_data = data[index]
        new_data.update(json_data)
        new_data['annotator'] = username
        existing_data = []

        category = json_data['category']
        save_category_info(category)

        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                existing_data = json.load(json_file)
        except FileNotFoundError:
            pass

        # Check for duplicates: overwrite if exists, append otherwise
        is_duplicate = False
        for idx, datas in enumerate(existing_data):
            if datas['id'] == new_data['id']:
                existing_data[idx] = new_data
                is_duplicate = True
                break

        if not is_duplicate:
            existing_data.append(new_data)

        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(existing_data, json_file, ensure_ascii=False)
        res = 'Saved' if not is_duplicate else 'Duplicate found, overwritten'
        return jsonify({'save_state': res})
    else:
        return jsonify({"error": "Request body must be in JSON format"}), 400


# ========== Dual-annotator comparison ==========

@app.route('/compare')
def compare_page():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect('/loginPage/')
    return render_template('compare.html', username=get_username())

@app.route('/api/compare', methods=['GET'])
def api_compare():
    """
    Compare annotations from two annotators.
    Returns: same annotations, only-user1, only-user2, and differing annotations.
    """
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Not logged in"}), 401

    users = list(USERS.keys())
    if len(users) < 2:
        return jsonify({"error": "At least two annotators required"}), 400

    user1, user2 = users[0], users[1]

    def load_user_annotations(username):
        """Load all annotations for a user (merge perf and no_perf)."""
        annotations = {}
        for path in [get_user_perf_path(username), get_user_no_perf_path(username)]:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    for item in items:
                        annotations[item['id']] = item
        return annotations

    ann1 = load_user_annotations(user1)
    ann2 = load_user_annotations(user2)

    all_ids = set(ann1.keys()) | set(ann2.keys())

    same = []
    diff = []
    only_user1 = []
    only_user2 = []

    for rid in sorted(all_ids):
        in1 = rid in ann1
        in2 = rid in ann2
        if in1 and in2:
            a1 = ann1[rid]
            a2 = ann2[rid]
            same_perf = a1.get('is_perf') == a2.get('is_perf')
            same_cat = sorted(a1.get('category', [])) == sorted(a2.get('category', []))
            same_reason = a1.get('reason', '').strip() == a2.get('reason', '').strip()
            if same_perf and same_cat and same_reason:
                same.append({
                    'id': rid,
                    'is_perf': a1.get('is_perf'),
                    'category': a1.get('category', []),
                    'reason': a1.get('reason', ''),
                })
            else:
                diff.append({
                    'id': rid,
                    user1: {
                        'is_perf': a1.get('is_perf'),
                        'category': a1.get('category', []),
                        'reason': a1.get('reason', ''),
                    },
                    user2: {
                        'is_perf': a2.get('is_perf'),
                        'category': a2.get('category', []),
                        'reason': a2.get('reason', ''),
                    }
                })
        elif in1:
            a1 = ann1[rid]
            only_user1.append({
                'id': rid,
                'is_perf': a1.get('is_perf'),
                'category': a1.get('category', []),
                'reason': a1.get('reason', ''),
            })
        else:
            a2 = ann2[rid]
            only_user2.append({
                'id': rid,
                'is_perf': a2.get('is_perf'),
                'category': a2.get('category', []),
                'reason': a2.get('reason', ''),
            })

    return jsonify({
        'user1': user1,
        'user2': user2,
        'total_user1': len(ann1),
        'total_user2': len(ann2),
        'same': same,
        'diff': diff,
        'only_user1': only_user1,
        'only_user2': only_user2,
        'stats': {
            'same_count': len(same),
            'diff_count': len(diff),
            'only_user1_count': len(only_user1),
            'only_user2_count': len(only_user2),
            'agreement_rate': round(len(same) / max(len(same) + len(diff), 1) * 100, 2),
        }
    })

@app.route('/api/export_diff', methods=['GET'])
def export_diff():
    """Export diff results as a JSON file."""
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Not logged in"}), 401

    with app.test_request_context():
        resp = api_compare()
        compare_data = resp.get_json()

    export_path = './annotation_diff_result.json'
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(compare_data, f, ensure_ascii=False, indent=2)

    return jsonify({'message': f'Diff results exported to {export_path}', 'path': export_path})

@app.route('/api/remove_same', methods=['POST'])
def remove_same_annotations():
    """
    Remove identical annotations from both annotators' results.
    Consensus annotations are saved to a separate file.
    """
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Not logged in"}), 401

    users = list(USERS.keys())
    user1, user2 = users[0], users[1]

    def load_user_annotations(username):
        annotations = {}
        for path in [get_user_perf_path(username), get_user_no_perf_path(username)]:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    for item in items:
                        annotations[item['id']] = item
        return annotations

    ann1 = load_user_annotations(user1)
    ann2 = load_user_annotations(user2)

    consensus = []
    diff_ids = set()

    for rid in set(ann1.keys()) & set(ann2.keys()):
        a1, a2 = ann1[rid], ann2[rid]
        same_perf = a1.get('is_perf') == a2.get('is_perf')
        same_cat = sorted(a1.get('category', [])) == sorted(a2.get('category', []))
        same_reason = a1.get('reason', '').strip() == a2.get('reason', '').strip()
        if same_perf and same_cat and same_reason:
            consensus.append(a1)
        else:
            diff_ids.add(rid)

    consensus_path = './annotation_consensus.json'
    with open(consensus_path, 'w', encoding='utf-8') as f:
        json.dump(consensus, f, ensure_ascii=False, indent=2)

    consensus_ids = {item['id'] for item in consensus}
    for username in [user1, user2]:
        for path in [get_user_perf_path(username), get_user_no_perf_path(username)]:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                remaining = [item for item in items if item['id'] not in consensus_ids]
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(remaining, f, ensure_ascii=False, indent=2)

    return jsonify({
        'message': f'Removed {len(consensus)} consensus annotations, saved to {consensus_path}',
        'consensus_count': len(consensus),
        'remaining_diff_count': len(diff_ids),
    })

@app.route('/api/user_stats', methods=['GET'])
def user_stats():
    """Get annotation progress statistics for each annotator."""
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Not logged in"}), 401

    stats = {}
    for username in USERS:
        perf_count = 0
        no_perf_count = 0
        perf_path = get_user_perf_path(username)
        no_perf_path = get_user_no_perf_path(username)
        if os.path.exists(perf_path):
            with open(perf_path, 'r', encoding='utf-8') as f:
                perf_count = len(json.load(f))
        if os.path.exists(no_perf_path):
            with open(no_perf_path, 'r', encoding='utf-8') as f:
                no_perf_count = len(json.load(f))
        idx, _ = read_index_info(username)
        stats[username] = {
            'perf_count': perf_count,
            'no_perf_count': no_perf_count,
            'total': perf_count + no_perf_count,
            'current_index': int(idx),
        }

    return jsonify(stats)


if __name__ == '__main__':
    app.run(debug=True)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
