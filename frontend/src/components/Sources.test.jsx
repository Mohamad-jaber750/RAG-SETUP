import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Sources from "./Sources";

const duplicateSources = [
  {
    page_number: 73,
    section_title: "6.7 Centralize Access Control",
    content: "Centralize access control through a directory service.",
  },
  {
    page_number: 32,
    section_title: "6.7 Centralize Access Control",
    content: "Centralize   access control through a directory service.",
  },
];

test("does not render duplicate citation passages", () => {
  render(<Sources sources={duplicateSources} />);

  expect(screen.getByRole("button", { name: "▱ 1 source" })).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: /Citation/ })).toHaveLength(1);
});
