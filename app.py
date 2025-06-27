import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
from zoo_auction_system import GameState, Player
from typing import List, Dict, Optional, Any, Tuple, Callable

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'very-secret-key')

# Configure SocketIO for production
socketio = SocketIO(app, cors_allowed_origins="*")

# Global game state
game_state = GameState(socketio_callback=None)
game_lock = threading.Lock()

def socketio_callback(event, data):
    """Callback function for game events to broadcast to all clients"""
    print(f"Broadcasting event: {event} with data: {data}")
    socketio.emit(event, data)

# =========== General Routes ===========
@app.route('/')
def login_page():
    """Renders the login page."""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    """Handles admin and player login."""
    username = request.form.get('username')
    password = request.form.get('password') # For admin

    admin_password = os.environ.get('ADMIN_PASSWORD', 'password')

    if username == 'admin' and password == admin_password: # Simple admin auth
        session['user_type'] = 'admin'
        session['username'] = 'admin'
        return redirect(url_for('admin_dashboard'))

    if username:
        session['user_type'] = 'player'
        session['username'] = username
        # Logic to add player to game
        with game_lock:
            if game_state:
                player_exists = any(p.name == username for p in game_state.players)
                if not player_exists:
                    # Find an available zoo for the new player
                    if game_state.available_zoos:
                        zoo_id = list(game_state.available_zoos.keys())[0]
                        zoo = game_state.available_zoos.pop(zoo_id)
                        new_player = Player(f"player_{len(game_state.players) + 1}", username, zoo, money=100)
                        new_player.is_human = True
                        game_state.add_player(new_player)
                        # Broadcast updated game state
                        socketio.emit('game_state_update', game_state.get_game_state_dict())
        return redirect(url_for('player_view'))
    
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    """Logs the user out."""
    session.clear()
    return redirect(url_for('login_page'))

# =========== Admin Routes ===========
@app.route('/admin')
def admin_dashboard():
    """Renders the admin dashboard."""
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_page'))
    return render_template('admin.html')

@app.route('/api/admin/game/initialize', methods=['POST'])
def initialize_game():
    """Admin action: Initialize and start a new game."""
    global game_state
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        with game_lock:
            game_state = GameState(socketio_callback=socketio_callback)
        
        socketio.emit('game_state_update', game_state.get_game_state_dict())
        return jsonify({'success': True, 'message': 'Game initialized successfully'})
    except Exception as e:
        print(f"Error initializing game: {e}")
        return jsonify({'success': False, 'message': f'Error initializing game: {str(e)}'}), 500

@app.route('/api/admin/game/start_auction_tier', methods=['POST'])
def start_auction_tier():
    """Admin action: Start a specific auction tier."""
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    tier = None
    if request.json:
        tier = request.json.get('tier')
    if not tier:
        return jsonify({'success': False, 'message': 'Tier not specified'}), 400

    with game_lock:
        if not game_state:
            return jsonify({'success': False, 'message': 'Game not initialized'}), 404
        
        try:
            game_state.current_phase = "auction"
            game_state.auction_manager.start_tier_auction(tier)
            
            updated_state = game_state.get_game_state_dict()
            socketio.emit('game_state_update', updated_state)
            return jsonify({'success': True, 'message': f'Tier {tier} auction started'})   
        except Exception as e:
            print(f"Error starting auction: {e}")
            return jsonify({'success': False, 'message': f'Error starting auction: {str(e)}'}), 500

@app.route('/api/admin/game/stop_auction', methods=['POST'])
def stop_auction():
    """Admin action: Stop the current auction."""
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    with game_lock:
        if not game_state:
            return jsonify({'success': False, 'message': 'Game not initialized'}), 404
        
        if game_state.current_phase != "auction":
            return jsonify({'success': False, 'message': 'No auction is currently running'}), 400
            
        try:
            # Stop the auction
            game_state.auction_manager.stop_current_auction()
            game_state.current_phase = "setup" 
            
            # Broadcast the updated state
            socketio.emit('game_state_update', game_state.get_game_state_dict())
            socketio.emit('auction_stopped', {'message': 'Auction has been stopped by admin'})
            
            return jsonify({'success': True, 'message': 'Auction stopped successfully'})
            
        except Exception as e:
            print(f"Error stopping auction: {e}")
            return jsonify({'success': False, 'message': f'Error stopping auction: {str(e)}'}), 500

# =========== Player Routes ===========
@app.route('/player')
def player_view():
    """Renders the player's game view."""
    if session.get('user_type') != 'player':
        return redirect(url_for('login_page'))
    return render_template('player.html', username=session.get('username'))

# =========== Shared API Routes ===========
@app.route('/api/game/status')
def get_game_status():
    """Get current game status for any user."""
    with game_lock:
        if not game_state:
            return jsonify({'error': 'Game not initialized'}), 404
        return jsonify(game_state.get_game_state_dict())

# =========== SocketIO Events ===========
@socketio.on('connect')
def handle_connect():
    """Handle new client connections."""
    print(f'Client connected: {session.get("username", "unknown")}')
    with game_lock:
        if game_state:
            emit('game_state_update', game_state.get_game_state_dict())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnections."""
    print(f'Client disconnected: {session.get("username", "unknown")}')

@socketio.on('request_game_state')
def handle_request_game_state():
    """Handle explicit requests for game state from clients."""
    print(f'Game state requested by: {session.get("username", "unknown")}')
    with game_lock:
        if game_state:
            emit('game_state_update', game_state.get_game_state_dict())

@socketio.on('place_bid')
def handle_socketio_bid(data):
    """Handle bid placement from a player."""
    if session.get('user_type') != 'player':
        emit('bid_result', {'success': False, 'message': 'Only players can bid.'})
        return

    player_name = session.get('username')
    animal_id = data.get('animal_id')
    bid_amount = data.get('bid_amount')
    
    print(f"Received bid from {player_name}: {bid_amount} for animal {animal_id}")
    
    if not all([player_name, animal_id is not None, bid_amount]):
        emit('bid_result', {'success': False, 'message': 'Missing required bid data.'})
        return

    with game_lock:
        if not game_state:
            emit('bid_result', {'success': False, 'message': 'Game not initialized.'})
            return
            
        if game_state.current_phase != "auction":
            emit('bid_result', {'success': False, 'message': 'No auction is currently active.'})
            return
            
        player = next((p for p in game_state.players if p.name == player_name), None)
        if not player:
            emit('bid_result', {'success': False, 'message': 'Player not found.'})
            return
        
        if not player.id:
            emit('bid_result', {'success': False, 'message': 'Player ID is invalid.'})
            return

        try:
            result: Dict[str, Any] = game_state.auction_manager.submit_bid(player.id, animal_id, bid_amount)
            
            # Send result back to the bidding player
            emit('bid_result', result)
            
            # If bid was successful, broadcast the update to all players
            if result.get('success'):
                bid_update_data = {
                    'animal_id': animal_id,
                    'highest_bid': bid_amount,
                    'highest_bidder': player_name
                }
                # Broadcast to all clients
                socketio.emit('bid_update', bid_update_data)
                
                # Also send updated game state
                socketio.emit('game_state_update', game_state.get_game_state_dict())
                
        except Exception as e:
            print(f"Error processing bid: {e}")
            emit('bid_result', {'success': False, 'message': f'Error processing bid: {str(e)}'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)