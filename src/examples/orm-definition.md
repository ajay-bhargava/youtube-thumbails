```typescript
import { integer, pgTable, varchar, timestamp, text, uuid, bigint } from "drizzle-orm/pg-core";

export const youtubeTable = pgTable("youtube_table", {
  youtubeLink: varchar("youtube_link", {length: 255}).notNull(), // Or appropriate length
  id: uuid("id").defaultRandom().primaryKey(),
  segmentsId: uuid("segments_id").references(() => segments.id).notNull(),
  transcriptId: uuid("transcript_id").references(() => transcripts.id).notNull(),
});

export const transcripts = pgTable("transcripts", {
  id: uuid("id").defaultRandom().primaryKey(),
  youtubeId: uuid("youtube_id").references(() => youtubeTable.id).notNull(), // Foreign key to youtubeTable
  fullText: text("full_text").notNull(),
});

export const segments = pgTable("segments", {
  id: uuid("id").defaultRandom().primaryKey(),
  item: integer("item").notNull(),
  start: bigint("start").notNull(), // Use bigint for potentially large timestamps
  storageUrl: text("storage_url").notNull(),
  youtubeId: uuid("youtube_id").references(() => youtubeTable.id).notNull(), // Foreign key back to youtubeTable
});
```