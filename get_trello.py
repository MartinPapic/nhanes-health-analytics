import os, json, urllib.request

def main():
    creds = {}
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                creds[k] = v.strip("\"'")
    
    auth = f"key={creds['TRELLO_API_KEY']}&token={creds['TRELLO_TOKEN']}"
    
    url = f"https://api.trello.com/1/members/me/boards?{auth}"
    boards = json.loads(urllib.request.urlopen(url).read().decode())
    
    board = next((b for b in boards if 'NHANES' in b['name']), None)
    if not board: return
    
    url = f"https://api.trello.com/1/boards/{board['id']}/cards?{auth}"
    cards = json.loads(urllib.request.urlopen(url).read().decode())
    
    with open('trello_cards_dump.txt', 'w', encoding='utf-8') as f:
        for c in cards:
            f.write(f"[{c['name']}]\n{c['desc']}\n")

if __name__ == '__main__':
    main()
