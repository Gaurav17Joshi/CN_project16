import redis

# Redis connection settings
# REDIS_HOST = 'localhost'
REDIS_HOST = '10.7.40.88'
REDIS_PORT = 6379

# Queue names
HIGH_PRIORITY_QUEUE = 'monitoring:high'
LOW_PRIORITY_QUEUE = 'monitoring:low'

def setup_redis():
    """Set up Redis queues for the monitoring system"""
    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        
        # Test connection
        redis_client.ping()
        print("Connected to Redis successfully")
        
        # Clear existing queues (for clean setup)
        redis_client.delete(HIGH_PRIORITY_QUEUE)
        redis_client.delete(LOW_PRIORITY_QUEUE)
        
        print(f"Cleared queues: {HIGH_PRIORITY_QUEUE}, {LOW_PRIORITY_QUEUE}")
        print("Redis setup complete")
        
    except redis.ConnectionError:
        print("Failed to connect to Redis. Make sure Redis server is running.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Setting up Redis for simple monitoring system...")
    setup_redis()