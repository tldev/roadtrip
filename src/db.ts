import { Database } from "bun:sqlite";
import { mkdirSync } from "node:fs";

const DATA_DIR = process.env.DATA_DIR ?? "./data-local";
mkdirSync(DATA_DIR, { recursive: true });

const db = new Database(`${DATA_DIR}/sabby.db`, { create: true });
db.exec("PRAGMA journal_mode = WAL;");
db.exec("PRAGMA foreign_keys = ON;");

db.exec(`
  CREATE TABLE IF NOT EXISTS location_pings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    label TEXT,
    ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
  );
  CREATE INDEX IF NOT EXISTS idx_location_ts ON location_pings(id DESC);

  CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    for_date TEXT,
    for_stop TEXT,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    submitter_name TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    reviewed_at TEXT,
    reviewer_note TEXT
  );
  CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status, id DESC);
`);

export type LocationPing = {
  id: number;
  lat: number;
  lng: number;
  label: string | null;
  ts: string;
};

export type Submission = {
  id: number;
  for_date: string | null;
  for_stop: string | null;
  name: string;
  description: string | null;
  url: string | null;
  submitter_name: string | null;
  status: "pending" | "approved" | "rejected";
  ts: string;
  reviewed_at: string | null;
  reviewer_note: string | null;
};

const stmts = {
  insertPing: db.prepare<LocationPing, [number, number, string | null]>(
    `INSERT INTO location_pings (lat,lng,label) VALUES (?,?,?) RETURNING *`,
  ),
  latestPing: db.prepare<LocationPing, []>(
    `SELECT * FROM location_pings ORDER BY id DESC LIMIT 1`,
  ),
  insertSubmission: db.prepare<
    Submission,
    [string | null, string | null, string, string | null, string | null, string | null]
  >(
    `INSERT INTO submissions (for_date,for_stop,name,description,url,submitter_name)
     VALUES (?,?,?,?,?,?) RETURNING *`,
  ),
  listSubmissionsByStatus: db.prepare<Submission, [string]>(
    `SELECT * FROM submissions WHERE status = ? ORDER BY id DESC`,
  ),
  getSubmission: db.prepare<Submission, [number]>(
    `SELECT * FROM submissions WHERE id = ?`,
  ),
  updateSubmission: db.prepare<Submission, [string, string | null, number]>(
    `UPDATE submissions
     SET status = ?,
         reviewed_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
         reviewer_note = ?
     WHERE id = ?
     RETURNING *`,
  ),
};

export function recordPing(lat: number, lng: number, label: string | null): LocationPing {
  const row = stmts.insertPing.get(lat, lng, label);
  if (!row) throw new Error("insert ping failed");
  return row;
}

export function getLatestPing(): LocationPing | null {
  return stmts.latestPing.get() ?? null;
}

export function recordSubmission(input: {
  for_date: string | null;
  for_stop: string | null;
  name: string;
  description: string | null;
  url: string | null;
  submitter_name: string | null;
}): Submission {
  const row = stmts.insertSubmission.get(
    input.for_date,
    input.for_stop,
    input.name,
    input.description,
    input.url,
    input.submitter_name,
  );
  if (!row) throw new Error("insert submission failed");
  return row;
}

export function listSubmissions(status: "pending" | "approved" | "rejected"): Submission[] {
  return stmts.listSubmissionsByStatus.all(status);
}

export function moderateSubmission(
  id: number,
  status: "approved" | "rejected",
  reviewerNote: string | null,
): Submission | null {
  return stmts.updateSubmission.get(status, reviewerNote, id) ?? null;
}

export function findSubmission(id: number): Submission | null {
  return stmts.getSubmission.get(id) ?? null;
}
