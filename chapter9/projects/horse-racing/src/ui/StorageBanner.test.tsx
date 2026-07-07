import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { StorageBanner } from "./StorageBanner";

afterEach(cleanup);

describe("StorageBanner", () => {
  it("visible이 true이면 안내를 노출한다", () => {
    render(<StorageBanner visible={true} />);
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("visible이 false이면 안내를 노출하지 않는다", () => {
    render(<StorageBanner visible={false} />);
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
