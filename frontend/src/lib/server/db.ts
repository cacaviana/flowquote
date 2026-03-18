import { MongoClient, type Db } from 'mongodb';
import { MONGODB_URI, MONGODB_DATABASE } from '$env/static/private';

let client: MongoClient;
let db: Db;

export async function getDb(): Promise<Db> {
  if (db) return db;

  client = new MongoClient(MONGODB_URI);
  await client.connect();
  db = client.db(MONGODB_DATABASE || 'flowquote');

  return db;
}
