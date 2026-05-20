"""
TX Network - TCP Host/Client for Tai Xiu & LAN Word Chaining & Caro XO
- First to open = HOST (Admin)
- Clients discover host via UDP broadcast
- Host stops when app closes
- Supports LAN Word Chaining (Nối Chữ) state management
- Supports Caro XO LAN Matchmaking & Multiplayer
- Thread-safe and crash-resistant
"""
import socket, json, threading, time, random

TCP_PORT = 54320
UDP_PORT = 54321
DISCOVER_INTERVAL = 2.0
CONNECT_TIMEOUT = 2.0

VN_WORDS = [
    "học sinh", "sinh viên", "viên tịch", "tịch thu", "thu hoạch", 
    "hoạch định", "định hướng", "hướng dẫn", "dẫn đường", "đường đi", 
    "đi học", "học tập", "tập làm", "làm việc", "việc nhà", 
    "nhà cửa", "cửa sổ", "sổ sách", "sách vở", "vở kịch", 
    "kịch bản", "bản đồ", "đồ chơi", "chơi game", "game thủ", 
    "thủ môn", "môn học", "học hỏi", "hỏi han", "han gỉ", 
    "gỉ sét", "sét đánh", "đánh trận", "trận đấu", "đấu tranh", 
    "tranh giành", "giành giật", "giật mình", "mình mẩy", "mẩy may", 
    "may mắn", "mắn đẻ", "đẻ con", "con cái", "cái bang", 
    "bang hội", "hội họp", "họp hành", "hành động", "động viên",
    "viên chức", "chức vụ", "vụ án", "án mạng", "mạng mẽo",
    "bò sữa", "sữa tươi", "tươi đẹp", "đẹp đẽ", "đoàn kết",
    "kết quả", "quả bóng", "bóng đá", "đá bóng", "bóng bàn"
]

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def discover_host(timeout=CONNECT_TIMEOUT):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        s.bind(("", UDP_PORT))
        s.settimeout(timeout)
        data, addr = s.recvfrom(512)
        msg = json.loads(data.decode())
        if msg.get("type") == "HOST_ANNOUNCE":
            return addr[0], msg.get("name", "?")
    except:
        pass
    finally:
        s.close()
    return None


class GameHost:
    def __init__(self, my_name: str, on_state_change=None):
        self.my_name = my_name
        self.on_state_change = on_state_change
        self._clients: list[socket.socket] = []
        self._player_conns = {} # conn -> name
        self._lock = threading.Lock()
        self._running = False

        self.state = {
            "host": my_name,
            "round": 1,
            "betting_open": True,
            "time_left": 30,
            "dice": [0, 0, 0],
            "result": "",
            "bets": {},       # name -> {"choice": choice, "amount": amount}
            "scores": {my_name: 10000},
            "game_scores": {my_name: {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}},
            "players": [my_name],
            "history": [],     # list of "Tai", "Xiu", "Hoa"
            
            # LAN Word Chaining State (Multiplayer 1v1 Matchmaking)
            "noichu_word": random.choice(VN_WORDS),
            "noichu_time_left": 15,
            "noichu_active": True,
            "noichu_chat": ["Hệ thống: Bắt đầu nối chữ LAN PvP! Đăng ký ghép cặp để chơi!"],
            
            "noichu_queue": [],     # list of {"name": name, "bet": bet}
            "noichu_games": {},     # game_id -> {player_a, player_b, current_word, turn, bet_a, bet_b, time_left, status}

            # Caro XO LAN Matchmaking
            "caro_queue": [],     # list of {"name": name, "bet": bet}
            "caro_games": {}      # game_id -> {player_x, player_o, board, turn, bet_x, bet_o, status}
        }

    def start(self):
        self._running = True
        threading.Thread(target=self._tcp_accept_loop, daemon=True).start()
        threading.Thread(target=self._udp_announce_loop, daemon=True).start()
        threading.Thread(target=self._timer_loop, daemon=True).start()

    def stop(self):
        self._running = False
        if hasattr(self, '_udp_sock') and self._udp_sock:
            try: self._udp_sock.close()
            except: pass
        if hasattr(self, '_tcp_srv') and self._tcp_srv:
            try: self._tcp_srv.close()
            except: pass
        with self._lock:
            for c in self._clients:
                try: c.close()
                except: pass
            self._clients.clear()
            self._player_conns.clear()

    def _udp_announce_loop(self):
        self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self._running:
            try:
                msg = json.dumps({"type": "HOST_ANNOUNCE", "name": self.my_name}).encode()
                self._udp_sock.sendto(msg, ("255.255.255.255", UDP_PORT))
            except:
                pass
            for _ in range(int(DISCOVER_INTERVAL * 10)):
                if not self._running: break
                time.sleep(0.1)
        try: self._udp_sock.close()
        except: pass

    def _tcp_accept_loop(self):
        self._tcp_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_srv.bind(("", TCP_PORT))
        self._tcp_srv.listen(16)
        self._tcp_srv.settimeout(1.0)
        while self._running:
            try:
                conn, addr = self._tcp_srv.accept()
                with self._lock:
                    if not self._running:
                        conn.close()
                        break
                    self._clients.append(conn)
                threading.Thread(target=self._client_handler, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except:
                break
        try: self._tcp_srv.close()
        except: pass

    def _client_handler(self, conn: socket.socket):
        buf = ""
        try:
            while self._running:
                data = conn.recv(4096).decode("utf-8", errors="ignore")
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            self._handle_cmd(json.loads(line), conn)
                        except Exception as ex:
                            print(f"[Host] Cmd error: {ex}")
        except:
            pass
        finally:
            with self._lock:
                if conn in self._clients:
                    self._clients.remove(conn)
                name = self._player_conns.pop(conn, None)
                if name:
                    if name in self.state["players"]:
                        self.state["players"].remove(name)
                    
                    # Clean up matchmaking queues if name disconnected
                    self.state["caro_queue"] = [q for q in self.state["caro_queue"] if q["name"] != name]
                    self.state["noichu_queue"] = [q for q in self.state["noichu_queue"] if q["name"] != name]

                    # Handle Caro forfeit if player disconnects
                    dead_games = []
                    for gid, g in self.state["caro_games"].items():
                        if g["status"] == "playing" and (g["player_x"] == name or g["player_o"] == name):
                            winner = g["player_o"] if g["player_x"] == name else g["player_x"]
                            bet_win = g["bet_x"] if winner == g["player_x"] else g["bet_o"]
                            bet_lost = g["bet_o"] if winner == g["player_x"] else g["bet_x"]
                            
                            payout = bet_win + bet_lost
                            fee = int(payout * 0.03)
                            self.state["scores"][winner] = self.state["scores"].get(winner, 10000) + (payout - fee)
                            
                            if winner not in self.state["game_scores"]:
                                self.state["game_scores"][winner] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            self.state["game_scores"][winner]["caro"] = self.state["game_scores"][winner].get("caro", 0) + (bet_lost - fee)
                            
                            if name not in self.state["game_scores"]:
                                self.state["game_scores"][name] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            self.state["game_scores"][name]["caro"] = self.state["game_scores"][name].get("caro", 0) - bet_lost

                            g["status"] = "ended"
                            self.state["noichu_chat"].append(f"Hệ thống: {name} đã thoát! {winner} thắng cuộc Caro (+{bet_lost - fee}đ)")
                            dead_games.append(gid)
                    
                    # Remove ended games
                    for gid in dead_games:
                        self.state["caro_games"].pop(gid, None)

                    # Handle Word Chaining forfeit if player disconnects
                    dead_nc_games = []
                    for gid, g in self.state["noichu_games"].items():
                        if g["status"] == "playing" and (g["player_a"] == name or g["player_b"] == name):
                            winner = g["player_b"] if name == g["player_a"] else g["player_a"]
                            bet_win = g["bet_a"] if winner == g["player_a"] else g["bet_b"]
                            bet_lost = g["bet_b"] if winner == g["player_a"] else g["bet_a"]
                            
                            payout = bet_win + bet_lost
                            fee = int(payout * 0.03)
                            self.state["scores"][winner] = self.state["scores"].get(winner, 10000) + (payout - fee)
                            
                            if winner not in self.state["game_scores"]:
                                self.state["game_scores"][winner] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            self.state["game_scores"][winner]["noichu"] = self.state["game_scores"][winner].get("noichu", 0) + (bet_lost - fee)
                            
                            if name not in self.state["game_scores"]:
                                self.state["game_scores"][name] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            self.state["game_scores"][name]["noichu"] = self.state["game_scores"][name].get("noichu", 0) - bet_lost

                            g["status"] = "ended"
                            self.state["noichu_chat"].append(f"Hệ thống: {name} đã thoát! {winner} thắng cuộc Nối Chữ (+{bet_lost - fee}đ)")
                            dead_nc_games.append(gid)

                    for gid in dead_nc_games:
                        self.state["noichu_games"].pop(gid, None)
                        
            self.broadcast_state()
            try: conn.close()
            except: pass

    def _timer_loop(self):
        while self._running:
            time.sleep(1.0)
            if not self._running:
                break
            with self._lock:
                # 1. Tai Xiu Timer
                if self.state["betting_open"]:
                    if self.state["time_left"] > 0:
                        self.state["time_left"] -= 1
                        if self.state["time_left"] == 0:
                            if self.state["dice"] == [0,0,0]:
                                self.state["dice"] = [random.randint(1,6) for _ in range(3)]
                            self._trigger_roll_calculation_locked()
                
                # 2. Word Chaining 1v1 Games Timer
                dead_nc_games = []
                for gid, g in list(self.state["noichu_games"].items()):
                    if g["status"] == "playing":
                        if g["time_left"] > 0:
                            g["time_left"] -= 1
                            if g["time_left"] == 0:
                                name_lost = g["turn"]
                                winner = g["player_b"] if name_lost == g["player_a"] else g["player_a"]
                                bet_win = g["bet_a"] if winner == g["player_a"] else g["bet_b"]
                                bet_lost = g["bet_b"] if winner == g["player_a"] else g["bet_a"]
                                
                                payout = bet_win + bet_lost
                                fee = int(payout * 0.03)
                                self.state["scores"][winner] = self.state["scores"].get(winner, 10000) + (payout - fee)
                                
                                if winner not in self.state["game_scores"]:
                                    self.state["game_scores"][winner] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                                self.state["game_scores"][winner]["noichu"] = self.state["game_scores"][winner].get("noichu", 0) + (bet_lost - fee)
                                
                                if name_lost not in self.state["game_scores"]:
                                    self.state["game_scores"][name_lost] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                                self.state["game_scores"][name_lost]["noichu"] = self.state["game_scores"][name_lost].get("noichu", 0) - bet_lost

                                g["status"] = "ended"
                                self.state["noichu_chat"].append(f"Hệ thống: {name_lost} hết thời gian! {winner} thắng cuộc Nối Chữ (+{bet_lost - fee}đ)")
                                dead_nc_games.append(gid)
                                
                for gid in dead_nc_games:
                    self.state["noichu_games"].pop(gid, None)

            self.broadcast_state()

    def _trigger_roll_calculation_locked(self):
        self.state["betting_open"] = False
        dice = self.state["dice"]
        
        total = sum(dice)
        is_bao = (dice[0] == dice[1] == dice[2])
        is_chan = (total % 2 == 0)
        is_le = (total % 2 != 0)
        is_tai = (total >= 11 and total <= 17 and not is_bao)
        is_xiu = (total >= 4 and total <= 10 and not is_bao)
        
        if is_bao:
            result = "Bao"
        else:
            result = "Tai" if is_tai else "Xiu"
            
        self.state["result"] = result
        self.state["history"].append(result)
        if len(self.state["history"]) > 32:
            self.state["history"].pop(0)

        # Process bets
        fee_rate = 0.03
        for player, bet_info in self.state["bets"].items():
            choice = bet_info.get("choice")
            amount = bet_info.get("amount", 100)
            
            won = False
            payout_ratio = 1
            if choice == "Tai":
                won = is_tai
            elif choice == "Xiu":
                won = is_xiu
            elif choice == "Chan":
                won = is_chan
            elif choice == "Le":
                won = is_le
            elif choice == "Bao":
                won = is_bao
                payout_ratio = 5
                
            if won:
                payout = amount * (payout_ratio + 1)
                fee = int(payout * fee_rate)
                delta = payout - fee
            else:
                delta = 0 # Already deducted on confirm
                
            self.state["scores"][player] = self.state["scores"].get(player, 10000) + delta
            
            # Sync to game scores breakdown
            if player not in self.state["game_scores"]:
                self.state["game_scores"][player] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
            net_win = (amount * payout_ratio - int(payout * fee_rate)) if won else -amount
            self.state["game_scores"][player]["taixiu"] = self.state["game_scores"][player].get("taixiu", 0) + net_win
            
        threading.Thread(target=self._auto_reset_delay, daemon=True).start()

    def _auto_reset_delay(self):
        time.sleep(6.0)
        if self._running:
            self.admin_reset()

    def _handle_cmd(self, msg: dict, conn: socket.socket):
        t = msg.get("type")
        name = msg.get("name", "?")

        if t == "JOIN":
            pts = msg.get("points", 10000)
            g_scores = msg.get("game_scores", {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0})
            with self._lock:
                if conn:
                    self._player_conns[conn] = name
                if name not in self.state["scores"] or name == "TX":
                    self.state["scores"][name] = pts
                if "game_scores" not in self.state:
                    self.state["game_scores"] = {}
                self.state["game_scores"][name] = g_scores
                if name not in self.state["players"]:
                    self.state["players"].append(name)
            self.broadcast_state()

        elif t == "BET":
            if self.state["betting_open"]:
                choice = msg.get("choice", "")
                amount = msg.get("amount", 100)
                with self._lock:
                    self.state["scores"][name] = self.state["scores"].get(name, 10000) - amount
                    self.state["bets"][name] = {"choice": choice, "amount": amount}
                self.broadcast_state()

        elif t == "CARO_JOIN":
            bet = msg.get("bet", 100)
            with self._lock:
                self.state["caro_queue"] = [q for q in self.state["caro_queue"] if q["name"] != name]
                self.state["caro_queue"].append({"name": name, "bet": bet})
                
                # Matchmaking
                if len(self.state["caro_queue"]) >= 2:
                    p1 = self.state["caro_queue"].pop(0)
                    p2 = self.state["caro_queue"].pop(0)
                    
                    gid = f"caro_{random.randint(1000, 9999)}"
                    # Deduct bet immediately from scores
                    self.state["scores"][p1["name"]] = self.state["scores"].get(p1["name"], 10000) - p1["bet"]
                    self.state["scores"][p2["name"]] = self.state["scores"].get(p2["name"], 10000) - p2["bet"]
                    
                    self.state["caro_games"][gid] = {
                        "player_x": p1["name"],
                        "player_o": p2["name"],
                        "board": [["" for _ in range(8)] for _ in range(8)],
                        "turn": p1["name"],
                        "bet_x": p1["bet"],
                        "bet_o": p2["bet"],
                        "status": "playing"
                    }
                    self.state["noichu_chat"].append(f"Hệ thống: Trận đấu Caro khởi tranh: {p1['name']} (X) vs {p2['name']} (O)!")
            self.broadcast_state()

        elif t == "CARO_LEAVE":
            with self._lock:
                self.state["caro_queue"] = [q for q in self.state["caro_queue"] if q["name"] != name]
            self.broadcast_state()

        elif t == "CARO_FORFEIT":
            gid = msg.get("game_id")
            dead_games = []
            with self._lock:
                g = self.state["caro_games"].get(gid)
                if g and g["status"] == "playing":
                    winner = g["player_o"] if name == g["player_x"] else g["player_x"]
                    bet_win = g["bet_x"] if winner == g["player_x"] else g["bet_o"]
                    bet_lost = g["bet_o"] if winner == g["player_x"] else g["bet_x"]
                    
                    payout = bet_win + bet_lost
                    fee = int(payout * 0.03)
                    self.state["scores"][winner] = self.state["scores"].get(winner, 10000) + (payout - fee)
                    
                    if winner not in self.state["game_scores"]:
                        self.state["game_scores"][winner] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                    self.state["game_scores"][winner]["caro"] = self.state["game_scores"][winner].get("caro", 0) + (bet_lost - fee)
                    
                    if name not in self.state["game_scores"]:
                        self.state["game_scores"][name] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                    self.state["game_scores"][name]["caro"] = self.state["game_scores"][name].get("caro", 0) - bet_lost

                    g["status"] = "ended"
                    self.state["noichu_chat"].append(f"Hệ thống: {name} đầu hàng! {winner} thắng cuộc Caro (+{bet_lost - fee}đ)")
                    dead_games.append(gid)
            for gid in dead_games:
                self.state["caro_games"].pop(gid, None)
            self.broadcast_state()

        elif t == "CARO_MOVE":
            gid = msg.get("game_id")
            r = msg.get("row")
            c = msg.get("col")
            dead_games = []
            with self._lock:
                g = self.state["caro_games"].get(gid)
                if g and g["status"] == "playing" and g["turn"] == name:
                    symbol = "X" if name == g["player_x"] else "O"
                    if g["board"][r][c] == "":
                        g["board"][r][c] = symbol
                        
                        # Check win
                        if self._check_caro_win(g["board"], symbol):
                            g["status"] = "ended"
                            g["winner"] = name
                            
                            winner = name
                            loser = g["player_o"] if name == g["player_x"] else g["player_x"]
                            bet_win = g["bet_x"] if winner == g["player_x"] else g["bet_o"]
                            bet_lost = g["bet_o"] if winner == g["player_x"] else g["bet_x"]
                            
                            payout = bet_win + bet_lost
                            fee = int(payout * 0.03)
                            self.state["scores"][winner] = self.state["scores"].get(winner, 10000) + (payout - fee)
                            
                            if winner not in self.state["game_scores"]:
                                self.state["game_scores"][winner] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            self.state["game_scores"][winner]["caro"] = self.state["game_scores"][winner].get("caro", 0) + (bet_lost - fee)
                            
                            if loser not in self.state["game_scores"]:
                                self.state["game_scores"][loser] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            self.state["game_scores"][loser]["caro"] = self.state["game_scores"][loser].get("caro", 0) - bet_lost

                            self.state["noichu_chat"].append(f"Hệ thống: {winner} đã THẮNG Caro trước {loser}! (+{bet_lost - fee}đ)")
                            dead_games.append(gid)
                        # Check draw
                        elif all(cell != "" for row in g["board"] for cell in row):
                            g["status"] = "ended"
                            b_x = g["bet_x"]
                            b_o = g["bet_o"]
                            
                            # Refund 50%
                            refund_x = int(b_x * 0.5)
                            refund_o = int(b_o * 0.5)
                            self.state["scores"][g["player_x"]] = self.state["scores"].get(g["player_x"], 10000) + refund_x
                            self.state["scores"][g["player_o"]] = self.state["scores"].get(g["player_o"], 10000) + refund_o
                            
                            p1, p2 = g["player_x"], g["player_o"]
                            if p1 not in self.state["game_scores"]: self.state["game_scores"][p1] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            if p2 not in self.state["game_scores"]: self.state["game_scores"][p2] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                            self.state["game_scores"][p1]["caro"] = self.state["game_scores"][p1].get("caro", 0) - refund_x
                            self.state["game_scores"][p2]["caro"] = self.state["game_scores"][p2].get("caro", 0) - refund_o
                            
                            self.state["noichu_chat"].append(f"Hệ thống: Trận đấu Caro hòa! Cả hai đấu thủ bị trừ 50% số điểm cược.")
                            dead_games.append(gid)
                        else:
                            # Toggle turn
                            g["turn"] = g["player_o"] if name == g["player_x"] else g["player_x"]
            for gid in dead_games:
                self.state["caro_games"].pop(gid, None)
            self.broadcast_state()

        elif t == "NOICHU_JOIN":
            bet = msg.get("bet", 100)
            with self._lock:
                self.state["noichu_queue"] = [q for q in self.state["noichu_queue"] if q["name"] != name]
                self.state["noichu_queue"].append({"name": name, "bet": bet})
                
                # Matchmaking
                if len(self.state["noichu_queue"]) >= 2:
                    p1 = self.state["noichu_queue"].pop(0)
                    p2 = self.state["noichu_queue"].pop(0)
                    
                    gid = f"nc_{random.randint(1000, 9999)}"
                    # Deduct bet immediately from scores
                    self.state["scores"][p1["name"]] = self.state["scores"].get(p1["name"], 10000) - p1["bet"]
                    self.state["scores"][p2["name"]] = self.state["scores"].get(p2["name"], 10000) - p2["bet"]
                    
                    self.state["noichu_games"][gid] = {
                        "player_a": p1["name"],
                        "player_b": p2["name"],
                        "current_word": random.choice(VN_WORDS),
                        "turn": p1["name"],
                        "bet_a": p1["bet"],
                        "bet_b": p2["bet"],
                        "time_left": 15,
                        "status": "playing"
                    }
                    self.state["noichu_chat"].append(f"Hệ thống: Trận đấu Nối Chữ 1v1 khởi tranh: {p1['name']} vs {p2['name']}! Từ khởi đầu: [{self.state['noichu_games'][gid]['current_word'].upper()}]")
            self.broadcast_state()

        elif t == "NOICHU_LEAVE":
            with self._lock:
                self.state["noichu_queue"] = [q for q in self.state["noichu_queue"] if q["name"] != name]
            self.broadcast_state()

        elif t == "NOICHU_FORFEIT":
            gid = msg.get("game_id")
            dead_nc_games = []
            with self._lock:
                g = self.state["noichu_games"].get(gid)
                if g and g["status"] == "playing":
                    winner = g["player_b"] if name == g["player_a"] else g["player_a"]
                    bet_win = g["bet_a"] if winner == g["player_a"] else g["bet_b"]
                    bet_lost = g["bet_b"] if winner == g["player_a"] else g["bet_a"]
                    
                    payout = bet_win + bet_lost
                    fee = int(payout * 0.03)
                    self.state["scores"][winner] = self.state["scores"].get(winner, 10000) + (payout - fee)
                    
                    if winner not in self.state["game_scores"]:
                        self.state["game_scores"][winner] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                    self.state["game_scores"][winner]["noichu"] = self.state["game_scores"][winner].get("noichu", 0) + (bet_lost - fee)
                    
                    if name not in self.state["game_scores"]:
                        self.state["game_scores"][name] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                    self.state["game_scores"][name]["noichu"] = self.state["game_scores"][name].get("noichu", 0) - bet_lost

                    g["status"] = "ended"
                    self.state["noichu_chat"].append(f"Hệ thống: {name} đầu hàng! {winner} thắng cuộc Nối Chữ (+{bet_lost - fee}đ)")
                    dead_nc_games.append(gid)
            for gid in dead_nc_games:
                self.state["noichu_games"].pop(gid, None)
            self.broadcast_state()

        elif t == "NOICHU_SUBMIT":
            gid = msg.get("game_id")
            word = msg.get("word", "").strip().lower()
            dead_nc_games = []
            
            with self._lock:
                g = self.state["noichu_games"].get(gid)
                if g and g["status"] == "playing" and g["turn"] == name:
                    # Check formatting
                    parts = word.split()
                    correct = False
                    last_syllable = g["current_word"].split()[-1]
                    
                    if len(parts) == 2 and parts[0] == last_syllable:
                        has_icon = False
                        for char in word:
                            val = ord(char)
                            if val > 0x1F000 or (0x2000 <= val <= 0x32FF):
                                has_icon = True
                                break
                        if not has_icon:
                            correct = True

                    if correct:
                        g["current_word"] = word
                        g["turn"] = g["player_b"] if name == g["player_a"] else g["player_a"]
                        g["time_left"] = 15
                        self.state["noichu_chat"].append(f"{name} nối đúng: '{word}' (Chuyển lượt)")
                    else:
                        winner = g["player_b"] if name == g["player_a"] else g["player_a"]
                        bet_win = g["bet_a"] if winner == g["player_a"] else g["bet_b"]
                        bet_lost = g["bet_b"] if winner == g["player_a"] else g["bet_a"]
                        
                        payout = bet_win + bet_lost
                        fee = int(payout * 0.03)
                        self.state["scores"][winner] = self.state["scores"].get(winner, 10000) + (payout - fee)
                        
                        if winner not in self.state["game_scores"]:
                            self.state["game_scores"][winner] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                        self.state["game_scores"][winner]["noichu"] = self.state["game_scores"][winner].get("noichu", 0) + (bet_lost - fee)
                        
                        if name not in self.state["game_scores"]:
                            self.state["game_scores"][name] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
                        self.state["game_scores"][name]["noichu"] = self.state["game_scores"][name].get("noichu", 0) - bet_lost

                        g["status"] = "ended"
                        self.state["noichu_chat"].append(f"✗ {name} nối sai: '{word}'! {winner} thắng cuộc Nối Chữ (+{bet_lost - fee}đ)")
                        dead_nc_games.append(gid)
            for gid in dead_nc_games:
                self.state["noichu_games"].pop(gid, None)
            self.broadcast_state()

        elif t == "ADMIN_RESULT":
            dice = msg.get("dice", [1,1,1])
            with self._lock:
                self.state["dice"] = dice
                self.state["time_left"] = 0
                self._trigger_roll_calculation_locked()
            self.broadcast_state()

        elif t == "ADMIN_ADD_SCORE":
            player = msg.get("player", "")
            pts = msg.get("pts", 0)
            with self._lock:
                self.state["scores"][player] = self.state["scores"].get(player, 10000) + pts
            self.broadcast_state()

        elif t == "ADMIN_RESET":
            with self._lock:
                self.state["round"] += 1
                self.state["betting_open"] = True
                self.state["time_left"] = 30
                self.state["dice"] = [0,0,0]
                self.state["result"] = ""
                self.state["bets"] = {}
            self.broadcast_state()

        elif t == "ADMIN_RESET_SCORES":
            with self._lock:
                for player in self.state["scores"]:
                    self.state["scores"][player] = 10000
                if "game_scores" in self.state:
                    for player in self.state["game_scores"]:
                        self.state["game_scores"][player] = {"taixiu": 0, "baucua": 0, "slots": 0, "caro": 0, "noichu": 0}
            self.broadcast_state()

    def _check_caro_win(self, board, player):
        sz = len(board)
        directions = [(1,0), (0,1), (1,1), (1,-1)]
        for r in range(sz):
            for c in range(sz):
                if board[r][c] != player:
                    continue
                for dr, dc in directions:
                    count = 1
                    for step in range(1, 5):
                        nr, nc = r + dr * step, c + dc * step
                        if 0 <= nr < sz and 0 <= nc < sz and board[nr][nc] == player:
                            count += 1
                        else:
                            break
                    if count >= 5:
                        return True
        return False

    def broadcast_state(self):
        with self._lock:
            try:
                state_copy = json.loads(json.dumps(self.state))
                data = (json.dumps({"type": "STATE", "state": state_copy}) + "\n").encode()
            except Exception as e:
                print(f"[Host] State lock error: {e}")
                return
        
        if self.on_state_change:
            try:
                self.on_state_change(state_copy)
            except Exception as e:
                print(f"[Host] Callback crash: {e}")

        dead = []
        with self._lock:
            for c in self._clients:
                try:
                    c.sendall(data)
                except:
                    dead.append(c)
            for c in dead:
                try: self._clients.remove(c)
                except: pass

    def admin_result(self, dice: list):
        self._handle_cmd({"type": "ADMIN_RESULT", "dice": dice}, None)

    def admin_add_score(self, player: str, pts: int):
        self._handle_cmd({"type": "ADMIN_ADD_SCORE", "player": player, "pts": pts}, None)

    def admin_reset(self):
        self._handle_cmd({"type": "ADMIN_RESET"}, None)

    def admin_reset_scores(self):
        self._handle_cmd({"type": "ADMIN_RESET_SCORES"}, None)

    def local_sync_scores(self, name: str, points: int, game_scores: dict):
        self._handle_cmd({"type": "JOIN", "name": name, "points": points, "game_scores": game_scores}, None)

    def local_bet(self, name: str, choice: str, amount: int):
        self._handle_cmd({"type": "BET", "name": name, "choice": choice, "amount": amount}, None)

    def local_caro_join(self, name: str, bet: int):
        self._handle_cmd({"type": "CARO_JOIN", "name": name, "bet": bet}, None)

    def local_caro_leave(self, name: str):
        self._handle_cmd({"type": "CARO_LEAVE", "name": name}, None)

    def local_caro_forfeit(self, name: str, game_id: str):
        self._handle_cmd({"type": "CARO_FORFEIT", "name": name, "game_id": game_id}, None)

    def local_caro_move(self, name: str, game_id: str, row: int, col: int):
        self._handle_cmd({"type": "CARO_MOVE", "name": name, "game_id": game_id, "row": row, "col": col}, None)

    def local_noichu_join(self, name: str, bet: int):
        self._handle_cmd({"type": "NOICHU_JOIN", "name": name, "bet": bet}, None)

    def local_noichu_leave(self, name: str):
        self._handle_cmd({"type": "NOICHU_LEAVE", "name": name}, None)

    def local_noichu_forfeit(self, name: str, game_id: str):
        self._handle_cmd({"type": "NOICHU_FORFEIT", "name": name, "game_id": game_id}, None)

    def local_noichu(self, name: str, game_id: str, word: str):
        self._handle_cmd({"type": "NOICHU_SUBMIT", "name": name, "game_id": game_id, "word": word}, None)


class GameClient:
    def __init__(self, host_ip: str, my_name: str, initial_points: int, game_scores: dict, on_state=None):
        self.host_ip = host_ip
        self.my_name = my_name
        self.initial_points = initial_points
        self.game_scores = game_scores
        self.on_state = on_state
        self._conn: socket.socket | None = None
        self._running = False

    def connect(self) -> bool:
        try:
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._conn.settimeout(3.0)
            self._conn.connect((self.host_ip, TCP_PORT))
            self._conn.settimeout(None)
            self._running = True
            threading.Thread(target=self._recv_loop, daemon=True).start()
            self._send({"type": "JOIN", "name": self.my_name, "points": self.initial_points, "game_scores": self.game_scores})
            return True
        except:
            return False

    def disconnect(self):
        self._running = False
        try:
            if self._conn: self._conn.close()
        except: pass

    def _send(self, msg: dict):
        try:
            data = (json.dumps(msg) + "\n").encode()
            self._conn.sendall(data)
        except: pass

    def bet(self, choice: str, amount: int):
        self._send({"type": "BET", "name": self.my_name, "choice": choice, "amount": amount})

    def caro_join(self, bet: int):
        self._send({"type": "CARO_JOIN", "name": self.my_name, "bet": bet})

    def caro_leave(self):
        self._send({"type": "CARO_LEAVE", "name": self.my_name})

    def caro_forfeit(self, game_id: str):
        self._send({"type": "CARO_FORFEIT", "name": self.my_name, "game_id": game_id})

    def caro_move(self, game_id: str, row: int, col: int):
        self._send({"type": "CARO_MOVE", "name": self.my_name, "game_id": game_id, "row": row, "col": col})

    def noichu_join(self, bet: int):
        self._send({"type": "NOICHU_JOIN", "name": self.my_name, "bet": bet})

    def noichu_leave(self):
        self._send({"type": "NOICHU_LEAVE", "name": self.my_name})

    def noichu_forfeit(self, game_id: str):
        self._send({"type": "NOICHU_FORFEIT", "name": self.my_name, "game_id": game_id})

    def submit_noichu(self, game_id: str, word: str):
        self._send({"type": "NOICHU_SUBMIT", "name": self.my_name, "game_id": game_id, "word": word})

    def admin_result(self, dice: list):
        self._send({"type": "ADMIN_RESULT", "dice": dice})

    def admin_add_score(self, player: str, pts: int):
        self._send({"type": "ADMIN_ADD_SCORE", "player": player, "pts": pts})

    def admin_reset(self):
        self._send({"type": "ADMIN_RESET"})

    def admin_reset_scores(self):
        self._send({"type": "ADMIN_RESET_SCORES"})

    def _recv_loop(self):
        buf = ""
        try:
            while self._running:
                chunk = self._conn.recv(4096).decode("utf-8", errors="ignore")
                if not chunk: break
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line and self.on_state:
                        msg = json.loads(line)
                        if msg.get("type") == "STATE":
                            self.on_state(msg["state"])
        except: pass
