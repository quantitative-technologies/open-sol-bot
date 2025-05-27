# Cache preload microservices

This microservice is responsible for preloading and maintaining various cached data to improve the performance of the main application.

## Project Structure

```
cache_preloader/
├── __init__.py           # Package initialization file
├── main.py               # Main entrance point
├── core/                 # Core Components
│   ├── __init__.py       # Core package initialization file
│   ├── protocols.py      # Protocol definition
│   └── base.py           # Basic class implementation
├── caches/               # Specific cache implementation
│   ├── __init__.py       # Cache package initialization file
│   ├── blockhash.py      # Block hash cache
│   ├── min_balance_rent.py # Minimum rental balance cache
│   └── raydium_pool.py   # Raydium Pool cache
└── services/             # Service implementation
    ├── __init__.py       # Service package initialization file
    └── auto_update_service.py # Automatic update service
```
## Component Description

### Core Components (core/)

- **protocols.py**: Define the protocol interface of the cache system
- **base.py**: Implement basic cache class and provide common functions

### Cache Implementation (caches/)

- **blockhash.py**: Block hash cache implementation
- **min_balance_rent.py**: Minimum rental balance cache implementation
- **raydium_pool.py**: Raydium pool cache implementation

### Service Implementation (services/)

- **auto_update_service.py**: Automatically update cache services, coordinate and manage updates of various caches