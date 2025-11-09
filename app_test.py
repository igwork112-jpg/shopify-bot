# # # ============================================================
# # # FILE: app.py - Flask Backend Server
# # # ============================================================
# # from flask import Flask, request, jsonify, send_from_directory
# # from flask_cors import CORS
# # import threading
# # import os
# # import time
# # from pathlib import Path

# # app = Flask(__name__, static_folder='.')
# # CORS(app)

# # # Global bot state
# # bot_state = {
# #     'running': False,
# #     'bot_instance': None,
# #     'logs': [],
# #     'stats': {
# #         'productsProcessed': 0,
# #         'reviewsPosted': 0,
# #         'reviewsFailed': 0,
# #         'collectionsProcessed': 0
# #     }
# # }

# # @app.route('/')
# # def index():
# #     """Serve the frontend HTML at http://127.0.0.1:5000"""
# #     return send_from_directory('.', 'frontend.html')

# # @app.route('/start-bot', methods=['POST'])
# # def start_bot():
# #     """Start the review bot with user configuration"""
# #     global bot_state
    
# #     if bot_state['running']:
# #         return jsonify({
# #             'success': False,
# #             'message': 'Bot is already running'
# #         }), 400
    
# #     try:
# #         # Get configuration from request
# #         config = request.json
        
# #         # Update .env file with new configuration
# #         env_path = Path('.env')
# #         env_content = f"""# Store Configuration
# # STORE_URL={config['storeUrl']}

# # # API Keys
# # OPENAI_API_KEY={config['apiKey']}

# # # Bot Settings
# # REVIEWS_PER_PRODUCT={config['reviewsPerProduct']}
# # USE_AI_IMAGES={'true' if config['useAiImages'] else 'false'}
# # HEADLESS={'true' if config['headless'] else 'false'}
# # MIN_DELAY=3
# # MAX_DELAY=6
# # """
        
# #         with open(env_path, 'w') as f:
# #             f.write(env_content)
        
# #         # Reset logs and stats
# #         bot_state['logs'] = []
# #         bot_state['stats'] = {
# #             'productsProcessed': 0,
# #             'reviewsPosted': 0,
# #             'reviewsFailed': 0,
# #             'collectionsProcessed': 0
# #         }
        
# #         # Start bot in separate thread
# #         bot_thread = threading.Thread(target=run_bot, daemon=True)
# #         bot_thread.start()
        
# #         bot_state['running'] = True
        
# #         return jsonify({
# #             'success': True,
# #             'message': 'Bot started successfully'
# #         })
        
# #     except Exception as e:
# #         return jsonify({
# #             'success': False,
# #             'message': str(e)
# #         }), 500

# # @app.route('/stop-bot', methods=['POST'])
# # def stop_bot():
# #     """Stop the running bot"""
# #     global bot_state
    
# #     if not bot_state['running']:
# #         return jsonify({
# #             'success': False,
# #             'message': 'Bot is not running'
# #         }), 400
    
# #     try:
# #         bot_state['running'] = False
# #         add_log('warning', 'Bot stop requested by user')
        
# #         return jsonify({
# #             'success': True,
# #             'message': 'Bot stop signal sent'
# #         })
        
# #     except Exception as e:
# #         return jsonify({
# #             'success': False,
# #             'message': str(e)
# #         }), 500

# # @app.route('/bot-status', methods=['GET'])
# # def bot_status():
# #     """Get current bot status and logs"""
# #     global bot_state
    
# #     # Get new logs since last request
# #     logs = bot_state['logs'].copy()
# #     bot_state['logs'] = []  # Clear logs after sending
    
# #     return jsonify({
# #         'running': bot_state['running'],
# #         'logs': logs,
# #         'productsProcessed': bot_state['stats']['productsProcessed'],
# #         'reviewsPosted': bot_state['stats']['reviewsPosted'],
# #         'reviewsFailed': bot_state['stats']['reviewsFailed'],
# #         'collectionsProcessed': bot_state['stats']['collectionsProcessed']
# #     })

# # def run_bot():
# #     """Run the main bot script"""
# #     global bot_state
    
# #     try:
# #         add_log('info', 'Initializing bot...')
        
# #         # Reload settings to get updated .env values
# #         from importlib import reload
# #         import config.settings
# #         reload(config.settings)
        
# #         # Import main module
# #         import main
# #         reload(main)
        
# #         add_log('success', 'Bot initialized successfully')
# #         add_log('info', 'Starting review automation...')
        
# #         # Create bot instance
# #         bot = main.ReviewBot()
# #         bot_state['bot_instance'] = bot
        
# #         # Wrap the stats dictionary to track updates
# #         original_stats = bot.stats
        
# #         class StatsTracker(dict):
# #             def __setitem__(self, key, value):
# #                 super().__setitem__(key, value)
# #                 # Update web interface stats
# #                 bot_state['stats']['productsProcessed'] = self.get('products_processed', 0)
# #                 bot_state['stats']['reviewsPosted'] = self.get('reviews_posted', 0)
# #                 bot_state['stats']['reviewsFailed'] = self.get('reviews_failed', 0)
# #                 bot_state['stats']['collectionsProcessed'] = self.get('collections_processed', 0)
                
# #                 # Check for web logs
# #                 if hasattr(main, 'web_logs') and main.web_logs:
# #                     for log in main.web_logs:
# #                         add_log(log['type'], log['message'])
# #                     main.web_logs.clear()
        
# #         # Replace stats with tracked version
# #         tracked_stats = StatsTracker(original_stats)
# #         bot.stats = tracked_stats
        
# #         # Run the bot
# #         bot.run()
        
# #         add_log('success', '🎉 Bot completed all tasks!')
# #         bot_state['running'] = False
        
# #     except KeyboardInterrupt:
# #         add_log('warning', 'Bot stopped by user')
# #         bot_state['running'] = False
# #     except Exception as e:
# #         import traceback
# #         error_msg = str(e)
# #         add_log('error', f'Bot error: {error_msg}')
# #         # Add traceback for debugging
# #         tb = traceback.format_exc()
# #         for line in tb.split('\n')[:5]:  # First 5 lines of traceback
# #             if line.strip():
# #                 add_log('error', line.strip())
# #         bot_state['running'] = False

# # def add_log(log_type, message):
# #     """Add a log entry"""
# #     bot_state['logs'].append({
# #         'type': log_type,
# #         'message': message,
# #         'timestamp': time.time()
# #     })
# #     # Also print to console
# #     print(f"[{log_type.upper()}] {message}")

# # if __name__ == '__main__':
# #     print("=" * 70)
# #     print("🚀 Review Bot Backend Server")
# #     print("=" * 70)
# #     print("✨ Frontend available at: http://127.0.0.1:5000")
# #     print("✨ Or open: http://localhost:5000")
# #     print("=" * 70)
# #     print("\nWaiting for commands from web interface...")
    
# #     app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

# # ============================================================
# # FILE: app.py - Flask Backend Server (Improved with Stop & Headless Control)
# # ============================================================
# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# import threading
# import os
# import time
# from pathlib import Path
# from importlib import reload

# app = Flask(__name__, static_folder='.')
# CORS(app)

# # Global bot state
# bot_state = {
#     'running': False,
#     'bot_instance': None,
#     'thread': None,
#     'logs': [],
#     'stats': {
#         'productsProcessed': 0,
#         'reviewsPosted': 0,
#         'reviewsFailed': 0,
#         'collectionsProcessed': 0
#     }
# }

# # Global stop flag
# stop_flag = False


# @app.route('/')
# def index():
#     """Serve frontend"""
#     return send_from_directory('.', 'frontend.html')


# @app.route('/start-bot', methods=['POST'])
# def start_bot():
#     """Start the review bot with user configuration"""
#     global bot_state, stop_flag

#     if bot_state['running']:
#         return jsonify({'success': False, 'message': 'Bot is already running'}), 400

#     try:
#         config = request.json
#         stop_flag = False  # Reset stop flag

#         # Update .env file dynamically
#         env_path = Path('.env')
#         env_content = f"""# Store Configuration
# STORE_URL={config['storeUrl']}

# # API Keys
# OPENAI_API_KEY={config['apiKey']}

# # Bot Settings
# REVIEWS_PER_PRODUCT={config['reviewsPerProduct']}
# USE_AI_IMAGES={'true' if config['useAiImages'] else 'false'}
# HEADLESS={'true' if config['headless'] else 'false'}
# MIN_DELAY=3
# MAX_DELAY=6
# """
#         with open(env_path, 'w') as f:
#             f.write(env_content)

#         # Reset logs and stats
#         bot_state['logs'].clear()
#         bot_state['stats'] = {
#             'productsProcessed': 0,
#             'reviewsPosted': 0,
#             'reviewsFailed': 0,
#             'collectionsProcessed': 0
#         }

#         # Start bot thread
#         bot_thread = threading.Thread(target=run_bot, daemon=True)
#         bot_thread.start()

#         bot_state['running'] = True
#         bot_state['thread'] = bot_thread

#         return jsonify({'success': True, 'message': 'Bot started successfully'})

#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500


# @app.route('/stop-bot', methods=['POST'])
# def stop_bot():
#     """Stop the running bot gracefully"""
#     global bot_state, stop_flag

#     if not bot_state['running']:
#         return jsonify({'success': False, 'message': 'Bot is not running'}), 400

#     try:
#         stop_flag = True  # Signal the bot to stop
#         add_log('warning', 'Stop signal sent — attempting graceful shutdown...')

#         # If bot instance exists, call its stop() if implemented
#         if bot_state['bot_instance'] and hasattr(bot_state['bot_instance'], 'stop'):
#             try:
#                 bot_state['bot_instance'].stop()
#                 add_log('info', 'Bot stop() method called successfully')
#             except Exception as e:
#                 add_log('error', f'Error while stopping bot: {e}')

#         bot_state['running'] = False
#         return jsonify({'success': True, 'message': 'Bot stop signal sent'})

#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500


# @app.route('/bot-status', methods=['GET'])
# def bot_status():
#     """Return live bot status"""
#     global bot_state
#     logs = bot_state['logs'].copy()
#     bot_state['logs'].clear()
#     return jsonify({
#         'running': bot_state['running'],
#         'logs': logs,
#         'productsProcessed': bot_state['stats']['productsProcessed'],
#         'reviewsPosted': bot_state['stats']['reviewsPosted'],
#         'reviewsFailed': bot_state['stats']['reviewsFailed'],
#         'collectionsProcessed': bot_state['stats']['collectionsProcessed']
#     })


# def run_bot():
#     """Main worker thread for Review Bot"""
#     global bot_state, stop_flag

#     try:
#         add_log('info', 'Initializing bot...')

#         import config.settings
#         reload(config.settings)
#         import main
#         reload(main)

#         add_log('success', 'Bot initialized successfully')
#         add_log('info', 'Starting review automation...')

#         bot = main.ReviewBot()
#         bot_state['bot_instance'] = bot

#         # Stats tracker
#         original_stats = bot.stats

#         class StatsTracker(dict):
#             def __setitem__(self, key, value):
#                 super().__setitem__(key, value)
#                 bot_state['stats']['productsProcessed'] = self.get('products_processed', 0)
#                 bot_state['stats']['reviewsPosted'] = self.get('reviews_posted', 0)
#                 bot_state['stats']['reviewsFailed'] = self.get('reviews_failed', 0)
#                 bot_state['stats']['collectionsProcessed'] = self.get('collections_processed', 0)

#                 # Web logs
#                 if hasattr(main, 'web_logs') and main.web_logs:
#                     for log in main.web_logs:
#                         add_log(log['type'], log['message'])
#                     main.web_logs.clear()

#         bot.stats = StatsTracker(original_stats)

#         # Run the bot until stop_flag is set
#         while not stop_flag:
#             bot.run()  # Your internal ReviewBot loop
#             time.sleep(2)

#         add_log('warning', 'Bot received stop signal — shutting down.')
#         bot.cleanup() if hasattr(bot, 'cleanup') else None

#     except Exception as e:
#         import traceback
#         add_log('error', f'Bot crashed: {e}')
#         for line in traceback.format_exc().split('\n')[:5]:
#             if line.strip():
#                 add_log('error', line.strip())

#     finally:
#         bot_state['running'] = False
#         add_log('info', 'Bot thread exited cleanly')


# def add_log(log_type, message):
#     """Append log entry"""
#     bot_state['logs'].append({
#         'type': log_type,
#         'message': message,
#         'timestamp': time.time()
#     })
#     print(f"[{log_type.upper()}] {message}")


# if __name__ == '__main__':
#     print("=" * 70)
#     print("🚀 Review Bot Backend Server")
#     print("=" * 70)
#     print("✨ Frontend available at: http://127.0.0.1:5000")
#     print("✨ Or open: http://localhost:5000")
#     print("=" * 70)
#     print("\nWaiting for commands from web interface...\n")
#     app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time
from pathlib import Path
from importlib import reload

app = Flask(__name__, static_folder='.')
CORS(app)

# Global bot state
bot_state = {
    'running': False,
    'bot_instance': None,
    'thread': None,
    'logs': [],
    'stats': {
        'productsProcessed': 0,
        'reviewsPosted': 0,
        'reviewsFailed': 0,
        'collectionsProcessed': 0
    }
}

@app.route('/')
def index():
    """Serve frontend"""
    return send_from_directory('.', 'frontend.html')

@app.route('/start-bot', methods=['POST'])
def start_bot():
    """Start the review bot with user configuration"""
    global bot_state

    if bot_state['running']:
        return jsonify({'success': False, 'message': 'Bot is already running'}), 400

    try:
        config = request.json

        # Update .env file dynamically
        env_path = Path('.env')
        env_content = f"""# Store Configuration
STORE_URL={config['storeUrl']}

# API Keys
OPENAI_API_KEY={config['apiKey']}

# Bot Settings
REVIEWS_PER_PRODUCT={config['reviewsPerProduct']}
USE_AI_IMAGES={'true' if config['useAiImages'] else 'false'}
HEADLESS={'false' if config['headless'] else 'true'}
MIN_DELAY=3
MAX_DELAY=6
"""
        with open(env_path, 'w') as f:
            f.write(env_content)

        add_log('info', '📝 Configuration saved to .env file')
        add_log('info', f"Headless Mode: {'Enabled' if config['headless'] else 'Disabled'}")
        add_log('info', f"AI Images: {'Enabled' if config['useAiImages'] else 'Disabled'}")

        # Reset logs and stats
        bot_state['logs'].clear()
        bot_state['stats'] = {
            'productsProcessed': 0,
            'reviewsPosted': 0,
            'reviewsFailed': 0,
            'collectionsProcessed': 0
        }

        # Start bot thread
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()

        bot_state['running'] = True
        bot_state['thread'] = bot_thread

        return jsonify({'success': True, 'message': 'Bot started successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    """Stop the running bot gracefully"""
    global bot_state

    if not bot_state['running']:
        return jsonify({'success': False, 'message': 'Bot is not running'}), 400

    try:
        add_log('warning', '🛑 Stop signal sent - stopping bot...')

        # Call stop on bot instance if exists
        if bot_state['bot_instance']:
            try:
                bot_state['bot_instance'].stop()
                add_log('success', '✅ Stop signal sent to bot successfully')
            except Exception as e:
                add_log('error', f'Error calling stop: {e}')
        
        # Also set the global stop flag in main module
        try:
            import main
            main.request_stop()
            add_log('info', 'Global stop flag set')
        except Exception as e:
            add_log('error', f'Error setting stop flag: {e}')

        return jsonify({'success': True, 'message': 'Stop signal sent to bot'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/bot-status', methods=['GET'])
def bot_status():
    """Return live bot status"""
    global bot_state
    logs = bot_state['logs'].copy()
    bot_state['logs'].clear()
    return jsonify({
        'running': bot_state['running'],
        'logs': logs,
        'productsProcessed': bot_state['stats']['productsProcessed'],
        'reviewsPosted': bot_state['stats']['reviewsPosted'],
        'reviewsFailed': bot_state['stats']['reviewsFailed'],
        'collectionsProcessed': bot_state['stats']['collectionsProcessed']
    })

def run_bot():
    """Main worker thread for Review Bot"""
    global bot_state

    try:
        add_log('info', '🚀 Initializing bot...')

        # Reload modules
        import config.settings
        reload(config.settings)
        import main
        reload(main)

        add_log('success', '✅ Bot initialized successfully')
        add_log('info', '▶️ Starting review automation...')

        bot = main.ReviewBot()
        bot_state['bot_instance'] = bot

        # Stats tracker
        original_stats = bot.stats

        class StatsTracker(dict):
            def __setitem__(self, key, value):
                super().__setitem__(key, value)
                bot_state['stats']['productsProcessed'] = self.get('products_processed', 0)
                bot_state['stats']['reviewsPosted'] = self.get('reviews_posted', 0)
                bot_state['stats']['reviewsFailed'] = self.get('reviews_failed', 0)
                bot_state['stats']['collectionsProcessed'] = self.get('collections_processed', 0)

                # Web logs
                if hasattr(main, 'web_logs') and main.web_logs:
                    for log in main.web_logs:
                        add_log(log['type'], log['message'])
                    main.web_logs.clear()

        bot.stats = StatsTracker(original_stats)

        # Run the bot (this will block until complete or stopped)
        bot.run()
        
        add_log('success', '🎉 Bot completed all tasks!')

    except Exception as e:
        import traceback
        add_log('error', f'❌ Bot crashed: {e}')
        for line in traceback.format_exc().split('\n')[:5]:
            if line.strip():
                add_log('error', line.strip())

    finally:
        bot_state['running'] = False
        bot_state['bot_instance'] = None
        add_log('info', '⏹️ Bot stopped')

def add_log(log_type, message):
    """Append log entry"""
    bot_state['logs'].append({
        'type': log_type,
        'message': message,
        'timestamp': time.time()
    })
    print(f"[{log_type.upper()}] {message}")

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Review Bot Backend Server")
    print("=" * 70)
    print("✨ Frontend available at: http://127.0.0.1:5000")
    print("✨ Or open: http://localhost:5000")
    print("=" * 70)
    print("\nWaiting for commands from web interface...\n")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)