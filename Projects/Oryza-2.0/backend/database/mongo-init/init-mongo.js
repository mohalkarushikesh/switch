// MongoDB initialization script for Oryza

// Switch to oryza_nosql database
db = db.getSiblingDB('oryza_nosql');

// Create collections with validators
db.createCollection('user_sessions', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['userId', 'token', 'createdAt', 'expiresAt'],
            properties: {
                userId: {
                    bsonType: 'string',
                    description: 'User ID from PostgreSQL'
                },
                token: {
                    bsonType: 'string',
                    description: 'Session token'
                },
                userAgent: {
                    bsonType: 'string'
                },
                ipAddress: {
                    bsonType: 'string'
                },
                createdAt: {
                    bsonType: 'date'
                },
                expiresAt: {
                    bsonType: 'date'
                },
                lastActivity: {
                    bsonType: 'date'
                }
            }
        }
    }
});

db.createCollection('audit_logs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['userId', 'action', 'timestamp'],
            properties: {
                userId: {
                    bsonType: 'string'
                },
                action: {
                    bsonType: 'string'
                },
                resource: {
                    bsonType: 'string'
                },
                resourceId: {
                    bsonType: 'string'
                },
                metadata: {
                    bsonType: 'object'
                },
                timestamp: {
                    bsonType: 'date'
                }
            }
        }
    }
});

db.createCollection('market_snapshots', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'data'],
            properties: {
                timestamp: {
                    bsonType: 'date'
                },
                data: {
                    bsonType: 'object',
                    properties: {
                        indices: {
                            bsonType: 'object'
                        },
                        topGainers: {
                            bsonType: 'array'
                        },
                        topLosers: {
                            bsonType: 'array'
                        },
                        mostActive: {
                            bsonType: 'array'
                        }
                    }
                }
            }
        }
    }
});

db.createCollection('ai_model_outputs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['modelName', 'version', 'input', 'output', 'timestamp'],
            properties: {
                modelName: {
                    bsonType: 'string'
                },
                version: {
                    bsonType: 'string'
                },
                userId: {
                    bsonType: 'string'
                },
                input: {
                    bsonType: 'object'
                },
                output: {
                    bsonType: 'object'
                },
                confidence: {
                    bsonType: 'double'
                },
                executionTime: {
                    bsonType: 'int'
                },
                timestamp: {
                    bsonType: 'date'
                }
            }
        }
    }
});

db.createCollection('user_preferences_extended', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['userId'],
            properties: {
                userId: {
                    bsonType: 'string'
                },
                watchedStocks: {
                    bsonType: 'array',
                    items: {
                        bsonType: 'object',
                        properties: {
                            symbol: { bsonType: 'string' },
                            addedAt: { bsonType: 'date' },
                            alerts: { bsonType: 'array' }
                        }
                    }
                },
                savedScreens: {
                    bsonType: 'array'
                },
                dashboardLayout: {
                    bsonType: 'object'
                },
                tradingPreferences: {
                    bsonType: 'object'
                }
            }
        }
    }
});

// Create indexes
db.user_sessions.createIndex({ userId: 1, createdAt: -1 });
db.user_sessions.createIndex({ token: 1 }, { unique: true });
db.user_sessions.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0 });

db.audit_logs.createIndex({ userId: 1, timestamp: -1 });
db.audit_logs.createIndex({ action: 1, timestamp: -1 });
db.audit_logs.createIndex({ timestamp: 1 }, { expireAfterSeconds: 7776000 }); // 90 days

db.market_snapshots.createIndex({ timestamp: -1 });
db.market_snapshots.createIndex({ timestamp: 1 }, { expireAfterSeconds: 604800 }); // 7 days

db.ai_model_outputs.createIndex({ userId: 1, modelName: 1, timestamp: -1 });
db.ai_model_outputs.createIndex({ timestamp: -1 });

db.user_preferences_extended.createIndex({ userId: 1 }, { unique: true });

// Insert sample data
db.market_snapshots.insertOne({
    timestamp: new Date(),
    data: {
        indices: {
            NIFTY: { value: 19845.5, change: 0.45, volume: 1234567890 },
            SENSEX: { value: 65782.3, change: 0.52, volume: 987654321 }
        },
        topGainers: [
            { symbol: 'RELIANCE', price: 2456.5, change: 2.3 },
            { symbol: 'TCS', price: 3480.75, change: 1.8 },
            { symbol: 'HDFC', price: 1625.4, change: 1.5 }
        ],
        topLosers: [
            { symbol: 'WIPRO', price: 420.3, change: -1.2 },
            { symbol: 'INFY', price: 1480.5, change: -0.8 },
            { symbol: 'BHARTIARTL', price: 845.2, change: -0.5 }
        ],
        mostActive: [
            { symbol: 'RELIANCE', volume: 12345678 },
            { symbol: 'TCS', volume: 8765432 },
            { symbol: 'SBIN', volume: 6543210 }
        ]
    }
});

print('MongoDB initialization completed successfully!'); 