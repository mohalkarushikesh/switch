-- Seed data for Oryza database
-- This creates initial data for testing and development

-- Insert test users
INSERT INTO users (email, username, password_hash, first_name, last_name, role, is_verified, email_verified_at) VALUES
('admin@oryza.com', 'admin', '$2b$10$YourHashedPasswordHere', 'Admin', 'User', 'admin', TRUE, CURRENT_TIMESTAMP),
('test@oryza.com', 'testuser', '$2b$10$YourHashedPasswordHere', 'Test', 'User', 'user', TRUE, CURRENT_TIMESTAMP),
('advisor@oryza.com', 'advisor1', '$2b$10$YourHashedPasswordHere', 'Financial', 'Advisor', 'advisor', TRUE, CURRENT_TIMESTAMP);

-- Get user IDs for reference
DO $$
DECLARE
    test_user_id UUID;
    admin_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@oryza.com';
    SELECT id INTO admin_user_id FROM users WHERE email = 'admin@oryza.com';
    
    -- Insert user preferences
    INSERT INTO user_preferences (user_id) VALUES 
    (test_user_id),
    (admin_user_id);
    
    -- Insert portfolios
    INSERT INTO portfolios (user_id, name, description, initial_value, current_value) VALUES
    (test_user_id, 'Growth Portfolio', 'High growth stocks focused portfolio', 1000000, 1250000),
    (test_user_id, 'Dividend Portfolio', 'Stable dividend paying stocks', 500000, 525000);
END $$;

-- Insert Indian stocks/securities
INSERT INTO securities (symbol, name, exchange, sector, industry, market_cap) VALUES
('RELIANCE', 'Reliance Industries Limited', 'NSE', 'Energy', 'Oil & Gas', 1800000000000),
('TCS', 'Tata Consultancy Services', 'NSE', 'Technology', 'IT Services', 1200000000000),
('INFY', 'Infosys Limited', 'NSE', 'Technology', 'IT Services', 600000000000),
('HDFCBANK', 'HDFC Bank Limited', 'NSE', 'Financial', 'Banking', 1100000000000),
('ITC', 'ITC Limited', 'NSE', 'Consumer Goods', 'FMCG', 500000000000),
('SBIN', 'State Bank of India', 'NSE', 'Financial', 'Banking', 450000000000),
('BHARTIARTL', 'Bharti Airtel Limited', 'NSE', 'Telecom', 'Telecommunications', 400000000000),
('KOTAKBANK', 'Kotak Mahindra Bank', 'NSE', 'Financial', 'Banking', 350000000000),
('LT', 'Larsen & Toubro', 'NSE', 'Industrial', 'Engineering', 300000000000),
('WIPRO', 'Wipro Limited', 'NSE', 'Technology', 'IT Services', 250000000000),
('BAJFINANCE', 'Bajaj Finance Limited', 'NSE', 'Financial', 'NBFC', 280000000000),
('TATAMOTORS', 'Tata Motors Limited', 'NSE', 'Automobile', 'Auto Manufacturer', 200000000000),
('MARUTI', 'Maruti Suzuki India Limited', 'NSE', 'Automobile', 'Auto Manufacturer', 350000000000),
('SUNPHARMA', 'Sun Pharmaceutical Industries', 'NSE', 'Healthcare', 'Pharmaceuticals', 220000000000),
('ADANIENT', 'Adani Enterprises Limited', 'NSE', 'Diversified', 'Conglomerate', 300000000000),
('NESTLEIND', 'Nestle India Limited', 'NSE', 'Consumer Goods', 'FMCG', 200000000000),
('ULTRACEMCO', 'UltraTech Cement Limited', 'NSE', 'Materials', 'Cement', 250000000000),
('POWERGRID', 'Power Grid Corporation', 'NSE', 'Utilities', 'Power', 150000000000),
('AXISBANK', 'Axis Bank Limited', 'NSE', 'Financial', 'Banking', 300000000000),
('TITAN', 'Titan Company Limited', 'NSE', 'Consumer Goods', 'Jewelry', 200000000000);

-- Create watchlists
DO $$
DECLARE
    test_user_id UUID;
    watchlist_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@oryza.com';
    
    -- Create default watchlist
    INSERT INTO watchlists (user_id, name, description, is_default) 
    VALUES (test_user_id, 'My Watchlist', 'Default watchlist for tracking favorite stocks', TRUE)
    RETURNING id INTO watchlist_id;
    
    -- Add items to watchlist
    INSERT INTO watchlist_items (watchlist_id, security_id, target_price) 
    SELECT 
        watchlist_id,
        s.id,
        CASE s.symbol
            WHEN 'RELIANCE' THEN 2600
            WHEN 'TCS' THEN 3600
            WHEN 'INFY' THEN 1500
            WHEN 'HDFCBANK' THEN 1700
            WHEN 'ITC' THEN 450
        END
    FROM securities s 
    WHERE s.symbol IN ('RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC');
END $$;

-- Create holdings
DO $$
DECLARE
    test_user_id UUID;
    growth_portfolio_id UUID;
    dividend_portfolio_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@oryza.com';
    SELECT id INTO growth_portfolio_id FROM portfolios WHERE user_id = test_user_id AND name = 'Growth Portfolio';
    SELECT id INTO dividend_portfolio_id FROM portfolios WHERE user_id = test_user_id AND name = 'Dividend Portfolio';
    
    -- Growth portfolio holdings
    INSERT INTO holdings (portfolio_id, security_id, quantity, average_price, current_price, invested_value, current_value)
    SELECT 
        growth_portfolio_id,
        s.id,
        CASE s.symbol
            WHEN 'RELIANCE' THEN 100
            WHEN 'TCS' THEN 50
            WHEN 'INFY' THEN 200
            WHEN 'WIPRO' THEN 150
            WHEN 'BHARTIARTL' THEN 100
        END,
        CASE s.symbol
            WHEN 'RELIANCE' THEN 2400
            WHEN 'TCS' THEN 3400
            WHEN 'INFY' THEN 1400
            WHEN 'WIPRO' THEN 400
            WHEN 'BHARTIARTL' THEN 800
        END,
        CASE s.symbol
            WHEN 'RELIANCE' THEN 2500
            WHEN 'TCS' THEN 3500
            WHEN 'INFY' THEN 1480
            WHEN 'WIPRO' THEN 420
            WHEN 'BHARTIARTL' THEN 850
        END,
        CASE s.symbol
            WHEN 'RELIANCE' THEN 240000
            WHEN 'TCS' THEN 170000
            WHEN 'INFY' THEN 280000
            WHEN 'WIPRO' THEN 60000
            WHEN 'BHARTIARTL' THEN 80000
        END,
        CASE s.symbol
            WHEN 'RELIANCE' THEN 250000
            WHEN 'TCS' THEN 175000
            WHEN 'INFY' THEN 296000
            WHEN 'WIPRO' THEN 63000
            WHEN 'BHARTIARTL' THEN 85000
        END
    FROM securities s 
    WHERE s.symbol IN ('RELIANCE', 'TCS', 'INFY', 'WIPRO', 'BHARTIARTL');
    
    -- Dividend portfolio holdings
    INSERT INTO holdings (portfolio_id, security_id, quantity, average_price, current_price, invested_value, current_value)
    SELECT 
        dividend_portfolio_id,
        s.id,
        CASE s.symbol
            WHEN 'ITC' THEN 500
            WHEN 'HDFCBANK' THEN 100
            WHEN 'SBIN' THEN 200
            WHEN 'POWERGRID' THEN 300
        END,
        CASE s.symbol
            WHEN 'ITC' THEN 420
            WHEN 'HDFCBANK' THEN 1550
            WHEN 'SBIN' THEN 580
            WHEN 'POWERGRID' THEN 240
        END,
        CASE s.symbol
            WHEN 'ITC' THEN 435
            WHEN 'HDFCBANK' THEN 1625
            WHEN 'SBIN' THEN 600
            WHEN 'POWERGRID' THEN 250
        END,
        CASE s.symbol
            WHEN 'ITC' THEN 210000
            WHEN 'HDFCBANK' THEN 155000
            WHEN 'SBIN' THEN 116000
            WHEN 'POWERGRID' THEN 72000
        END,
        CASE s.symbol
            WHEN 'ITC' THEN 217500
            WHEN 'HDFCBANK' THEN 162500
            WHEN 'SBIN' THEN 120000
            WHEN 'POWERGRID' THEN 75000
        END
    FROM securities s 
    WHERE s.symbol IN ('ITC', 'HDFCBANK', 'SBIN', 'POWERGRID');
END $$;

-- Create goals
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@oryza.com';
    
    INSERT INTO goals (user_id, name, description, target_amount, current_amount, target_date, monthly_contribution, category, priority) VALUES
    (test_user_id, 'Retirement Fund', 'Build a corpus for comfortable retirement', 50000000, 5000000, '2050-01-01', 100000, 'retirement', 10),
    (test_user_id, 'Dream Home', 'Save for down payment on dream home', 10000000, 3000000, '2028-01-01', 150000, 'real_estate', 8),
    (test_user_id, 'Children Education', 'Fund for children higher education', 5000000, 1000000, '2035-01-01', 50000, 'education', 9),
    (test_user_id, 'World Tour', 'Save for family world tour', 1000000, 200000, '2026-01-01', 40000, 'travel', 5),
    (test_user_id, 'Emergency Fund', '12 months of expenses', 2400000, 1800000, '2025-01-01', 50000, 'emergency', 10);
END $$;

-- Create sample notifications
DO $$
DECLARE
    test_user_id UUID;
BEGIN
    SELECT id INTO test_user_id FROM users WHERE email = 'test@oryza.com';
    
    INSERT INTO notifications (user_id, type, category, title, message, metadata) VALUES
    (test_user_id, 'success', 'trading', 'Order Executed', 'Your buy order for 100 shares of RELIANCE has been executed at ₹2,450', '{"orderId": "ORD123456", "symbol": "RELIANCE", "quantity": 100, "price": 2450}'::jsonb),
    (test_user_id, 'alert', 'portfolio', 'Price Alert Triggered', 'TCS has reached your target price of ₹3,500', '{"symbol": "TCS", "targetPrice": 3500, "currentPrice": 3505}'::jsonb),
    (test_user_id, 'info', 'advisory', 'New Recommendation', 'Based on your risk profile, we recommend rebalancing your portfolio', '{"recommendationType": "rebalance"}'::jsonb),
    (test_user_id, 'warning', 'market', 'Market Volatility Alert', 'High volatility detected in your portfolio holdings', '{"volatilityIndex": 25.5}'::jsonb);
END $$;

-- Create sample news articles
INSERT INTO news_articles (title, summary, source, url, published_at, sentiment_score, sentiment_label, impact_score, category) VALUES
('RBI Maintains Repo Rate at 6.5% in Latest Policy Meeting', 'The Reserve Bank of India kept the repo rate unchanged citing inflation concerns', 'Economic Times', 'https://example.com/news/1', CURRENT_TIMESTAMP - INTERVAL '2 hours', 0.45, 'neutral', 0.8, 'monetary-policy'),
('Reliance Announces Major Green Energy Investment', 'Reliance Industries unveils ₹75,000 crore investment plan for green energy', 'Business Standard', 'https://example.com/news/2', CURRENT_TIMESTAMP - INTERVAL '4 hours', 0.85, 'positive', 0.9, 'corporate'),
('IT Sector Faces Headwinds as US Recession Fears Mount', 'Major IT companies report slower deal closures', 'Mint', 'https://example.com/news/3', CURRENT_TIMESTAMP - INTERVAL '6 hours', 0.25, 'negative', 0.7, 'technology'),
('Electric Vehicle Sales Surge 150% YoY in India', 'EV adoption accelerates with government incentives', 'Financial Express', 'https://example.com/news/4', CURRENT_TIMESTAMP - INTERVAL '8 hours', 0.92, 'positive', 0.6, 'auto');

-- Map news to relevant securities
DO $$
DECLARE
    reliance_id UUID;
    tcs_id UUID;
    infy_id UUID;
    wipro_id UUID;
    tatamotors_id UUID;
    news1_id UUID;
    news2_id UUID;
    news3_id UUID;
    news4_id UUID;
BEGIN
    SELECT id INTO reliance_id FROM securities WHERE symbol = 'RELIANCE';
    SELECT id INTO tcs_id FROM securities WHERE symbol = 'TCS';
    SELECT id INTO infy_id FROM securities WHERE symbol = 'INFY';
    SELECT id INTO wipro_id FROM securities WHERE symbol = 'WIPRO';
    SELECT id INTO tatamotors_id FROM securities WHERE symbol = 'TATAMOTORS';
    
    SELECT id INTO news2_id FROM news_articles WHERE title LIKE '%Reliance%' LIMIT 1;
    SELECT id INTO news3_id FROM news_articles WHERE title LIKE '%IT Sector%' LIMIT 1;
    SELECT id INTO news4_id FROM news_articles WHERE title LIKE '%Electric Vehicle%' LIMIT 1;
    
    -- Map news to securities
    INSERT INTO news_securities (news_id, security_id, relevance_score) VALUES
    (news2_id, reliance_id, 1.0),
    (news3_id, tcs_id, 0.9),
    (news3_id, infy_id, 0.9),
    (news3_id, wipro_id, 0.9),
    (news4_id, tatamotors_id, 0.95);
END $$; 