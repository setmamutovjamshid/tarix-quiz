-- Neon (PostgreSQL) sxema fayli
-- Ushbu skript savollar jadvalini yaratadi va 3 ta namunaviy savol qo'shadi.

CREATE TABLE IF NOT EXISTS questions (
  id SERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  correct SMALLINT NOT NULL CHECK (correct BETWEEN 0 AND 3),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indeks: 1000+ savollarda tezkor ishlash va saralash uchun
CREATE INDEX IF NOT EXISTS idx_questions_created_at ON questions(created_at);

-- Namunaviy 3 ta savol (agar jadval bo'sh bo'lsa qo'shish)
INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct)
SELECT 
  'Oʻzbekiston Respublikasi mustaqillikka qachon erishgan?', 
  '1990-yil 1-sentyabr', 
  '1991-yil 1-sentyabr', 
  '1992-yil 8-dekabr', 
  '1993-yil 2-iyul', 
  1
WHERE NOT EXISTS (SELECT 1 FROM questions WHERE question = 'Oʻzbekiston Respublikasi mustaqillikka qachon erishgan?');

INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct)
SELECT 
  'Python dasturlash tilining asoschisi kim?', 
  'Gvido van Rossum (Guido van Rossum)', 
  'Brendan Eich', 
  'Jeyms Gosling', 
  'Bjarne Stroustrup', 
  0
WHERE NOT EXISTS (SELECT 1 FROM questions WHERE question = 'Python dasturlash tilining asoschisi kim?');

INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct)
SELECT 
  'Dunyodagi eng katta va eng chuqur okean qaysi?', 
  'Atlantika okeani', 
  'Hind okeani', 
  'Shimoliy Muz okeani', 
  'Tinch okeani', 
  3
WHERE NOT EXISTS (SELECT 1 FROM questions WHERE question = 'Dunyodagi eng katta va eng chuqur okean qaysi?');
