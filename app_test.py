# ============================================================
# FILE: app.py - Flask Backend Server
# ============================================================
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import os
import time
import sys
from pathlib import Path

app = Flask(__name__, static_folder='.')
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Global bot state
bot_state = {
    'running': False,
    'bot_instance': None,
    'bot_thread': None,
    'stop_requested': False,
    'logs': [],
    'stats': {
        'productsProcessed': 0,
        'reviewsPosted': 0,
        'reviewsFailed': 0,
        'collectionsProcessed': 0
    }
}


# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    """Serve the frontend HTML at http://127.0.0.1:5000"""
    return send_from_directory('.', 'frontend.html')


@app.route('/update-config', methods=['POST', 'OPTIONS'])
def update_config():
    """Update a specific configuration field in .env"""
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"[UPDATE-CONFIG] Received request")
        data = request.json
        print(f"[UPDATE-CONFIG] Data: {data}")
        field = data.get('field')
        value = data.get('value')

        if not field or value is None:
            print(f"[UPDATE-CONFIG] Missing field or value")
            return jsonify({'success': False, 'message': 'Missing field or value'}), 400

        env_path = Path('.env')
        env_content = {}

        # Read current .env file
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        env_content[key.strip()] = val.strip()

        # Update the field
        env_content[field] = value

        # Write back to .env
        with open(env_path, 'w') as f:
            f.write("# Store Configuration\n")
            if 'STORE_URL' in env_content:
                f.write(f"STORE_URL={env_content['STORE_URL']}\n")

            f.write("\n# API Keys\n")
            if 'OPENAI_API_KEY' in env_content:
                f.write(f"OPENAI_API_KEY={env_content['OPENAI_API_KEY']}\n")

            f.write("\n# Bot Settings\n")
            f.write(f"REVIEWS_PER_PRODUCT={env_content.get('REVIEWS_PER_PRODUCT', '3')}\n")
            f.write(f"USE_AI_IMAGES={env_content.get('USE_AI_IMAGES', 'true')}\n")
            f.write(f"HEADLESS={env_content.get('HEADLESS', 'false')}\n")
            f.write(f"MIN_DELAY={env_content.get('MIN_DELAY', '3')}\n")
            f.write(f"MAX_DELAY={env_content.get('MAX_DELAY', '6')}\n")

        # Force reload environment variables
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Clear the settings module from cache
        if 'config.settings' in sys.modules:
            del sys.modules['config.settings']

        add_log('info', f'Configuration updated: {field} = {value}')
        print(f"[UPDATE-CONFIG] Success: {field} updated")

        return jsonify({'success': True, 'message': f'{field} updated successfully'})

    except Exception as e:
        print(f"[UPDATE-CONFIG] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/start-bot', methods=['POST', 'OPTIONS'])
def start_bot():
    """Start the review bot with user configuration"""
    # Handle preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    global bot_state

    print(f"[START-BOT] Received request")
    
    if bot_state['running']:
        print(f"[START-BOT] Bot already running")
        return jsonify({'success': False, 'message': 'Bot is already running'}), 400

    try:
        config = request.json
        print(f"[START-BOT] Config received: {config}")

        # Write new .env file
        env_path = Path('.env')
        env_content = f"""# Store Configuration
STORE_URL={config['storeUrl']}

# API Keys
OPENAI_API_KEY={config['apiKey']}

# Bot Settings
REVIEWS_PER_PRODUCT={config['reviewsPerProduct']}
USE_AI_IMAGES={'true' if config['useAiImages'] else 'false'}
HEADLESS=true
MIN_DELAY=3
MAX_DELAY=6
"""
        with open(env_path, 'w') as f:
            f.write(env_content)

        # Force reload environment variables immediately
        from dotenv import load_dotenv
        load_dotenv(override=True)

        # Reset bot state
        bot_state.update({
            'logs': [],
            'stop_requested': False,
            'stats': {
                'productsProcessed': 0,
                'reviewsPosted': 0,
                'reviewsFailed': 0,
                'collectionsProcessed': 0
            }
        })

        # Start bot in new thread
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        bot_state['bot_thread'] = bot_thread
        bot_state['running'] = True

        print(f"[START-BOT] Bot started successfully")
        return jsonify({'success': True, 'message': 'Bot started successfully'})

    except Exception as e:
        print(f"[START-BOT] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    """Stop the running bot"""
    global bot_state

    if not bot_state['running']:
        return jsonify({'success': False, 'message': 'Bot is not running'}), 400

    try:
        bot_state['stop_requested'] = True
        bot_state['running'] = False
        add_log('warning', 'Bot stop requested by user')
        
        # Clear cached modules for clean restart
        modules_to_clear = ['config.settings', 'main', 'config']
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        return jsonify({'success': True, 'message': 'Bot stop signal sent'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/bot-status', methods=['GET'])
def bot_status():
    """Return current bot status and logs"""
    global bot_state
    logs = bot_state['logs'].copy()
    bot_state['logs'] = []
    return jsonify({
        'running': bot_state['running'],
        'logs': logs,
        **bot_state['stats']
    })


# ============================================================
# BOT EXECUTION LOGIC
# ============================================================

def run_bot():
    """Run the main bot script"""
    global bot_state

    try:
        add_log('info', 'Initializing bot...')

        # CRITICAL: Force reload .env and clear all cached modules
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # Clear ALL related modules from cache
        modules_to_clear = ['config.settings', 'main', 'config']
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Now import fresh settings
        from config.settings import settings
        
        # Verify we have the right URL
        add_log('info', f'✓ Loaded store URL from .env: {settings.STORE_URL}')
        add_log('info', f'✓ OpenAI API Key: {"*" * 20}{settings.OPENAI_API_KEY[-10:] if len(settings.OPENAI_API_KEY) > 10 else "SET"}')
        add_log('info', f'✓ Reviews per product: {settings.REVIEWS_PER_PRODUCT}')
        add_log('info', f'✓ AI Images: {settings.USE_AI_IMAGES}')
        add_log('info', f'✓ Headless mode: {settings.HEADLESS}')

        # Import main module (fresh)
        import main

        add_log('success', 'Bot initialized successfully')
        add_log('info', 'Starting review automation...')

        # Create bot instance with FRESH store URL from settings
        store_url = settings.STORE_URL
        add_log('info', f'🎯 Creating bot for store: {store_url}')

        bot = main.ReviewBot(store_url=store_url)
        bot_state['bot_instance'] = bot

        # Stats tracking
        original_stats = bot.stats

        class StatsTracker(dict):
            def __setitem__(self, key, value):
                super().__setitem__(key, value)
                bot_state['stats']['productsProcessed'] = self.get('products_processed', 0)
                bot_state['stats']['reviewsPosted'] = self.get('reviews_posted', 0)
                bot_state['stats']['reviewsFailed'] = self.get('reviews_failed', 0)
                bot_state['stats']['collectionsProcessed'] = self.get('collections_processed', 0)

                if hasattr(main, 'web_logs') and main.web_logs:
                    for log in main.web_logs:
                        add_log(log['type'], log['message'])
                    main.web_logs.clear()

                if bot_state['stop_requested']:
                    add_log('warning', 'Stop signal detected - halting bot...')
                    raise KeyboardInterrupt("Stop requested by user")

        bot.stats = StatsTracker(original_stats)
        
        # Run the bot
        add_log('info', '▶️  Bot execution starting...')
        bot.run()

        add_log('success', '🎉 Bot completed all tasks!')
        bot_state['running'] = False

    except KeyboardInterrupt:
        add_log('warning', 'Bot stopped by user')
        bot_state['running'] = False
    except Exception as e:
        import traceback
        add_log('error', f'❌ Bot error: {e}')
        tb = traceback.format_exc()
        for line in tb.split('\n')[:10]:  # Show first 10 lines of traceback
            if line.strip():
                add_log('error', line.strip())
        bot_state['running'] = False


def add_log(log_type, message):
    """Add log entry"""
    bot_state['logs'].append({'type': log_type, 'message': message, 'timestamp': time.time()})
    print(f"[{log_type.upper()}] {message}")


# ============================================================
# MAIN ENTRY
# ============================================================

if __name__ == '__main__':
    import os
    
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 70)
    print("🚀 Review Bot Backend Server")
    print("=" * 70)
    print(f"✨ Server running on port: {port}")
    print("✨ Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    print("=" * 70)
    print("\n⚙️  Configuration will be loaded from .env file")
    print("💡 Use the web interface to update settings")
    print("\nWaiting for commands from web interface...")
    
    # Use dynamic port and bind to 0.0.0.0 for Railway
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)