-- Supabase SQL Schema for Pickleball Courts
CREATE TABLE IF NOT EXISTS pickleball_courts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT,
    address TEXT UNIQUE,
    addresslink TEXT,
    telephone TEXT,
    websitetext TEXT,
    websitelink TEXT,
    courtimage_url TEXT UNIQUE,
    courtimage_path TEXT,
    courtimage_type TEXT,
    image_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_pickleball_courts_name ON pickleball_courts(name);
CREATE INDEX IF NOT EXISTS idx_pickleball_courts_created_at ON pickleball_courts(created_at);

-- Enable Row Level Security (optional)
ALTER TABLE pickleball_courts ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed)
CREATE POLICY "Allow all operations" ON pickleball_courts FOR ALL USING (true);