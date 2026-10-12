import postgres from "postgres";

// One client per server process; reused across dev hot reloads.
const holder = globalThis as { __stSql?: postgres.Sql };

export function db(): postgres.Sql {
  if (!holder.__stSql) {
    const url = process.env.DATABASE_URL;
    if (!url) throw new Error("DATABASE_URL is not set (see web/.env.example)");
    holder.__stSql = postgres(url, { max: 5 });
  }
  return holder.__stSql;
}
