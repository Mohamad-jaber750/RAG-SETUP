import { z } from "zod";

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  displayName: z.string().nullable().optional(),
  avatarUrl: z.string().url().nullable().optional(),
});

export const sourceSchema = z
  .object({
    page_number: z.number().nullable().optional(),
    section_title: z.string().nullable().optional(),
    filename: z.string().nullable().optional(),
    content: z.string().default(""),
  })
  .passthrough();

export const messageSchema = z
  .object({
    id: z.string(),
    role: z.enum(["user", "assistant"]),
    content: z.string(),
    sources: z.array(sourceSchema).optional().default([]),
  })
  .passthrough();

export const conversationSchema = z
  .object({
    _id: z.string(),
    title: z.string(),
    messages: z.array(messageSchema).optional().default([]),
  })
  .passthrough();

export const conversationsResponseSchema = z.object({
  conversations: z.array(conversationSchema),
});

export const conversationResponseSchema = z.object({
  conversation: conversationSchema,
});

export const logoutResponseSchema = z.object({
  logged_out: z.boolean(),
});
