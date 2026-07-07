import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { GameSettings } from "../persistence/schema";
import { SettingsPanel } from "./SettingsPanel";

afterEach(cleanup);

const SETTINGS: GameSettings = { horseCount: 5, muted: false };

describe("SettingsPanel", () => {
  it("출전마 수를 4~8 범위에서만 선택할 수 있다", () => {
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={0}
        onSettingsChange={vi.fn()}
        onReset={vi.fn()}
      />,
    );

    const select = screen.getByLabelText("출전마 수") as HTMLSelectElement;
    const values = Array.from(select.options).map((option) => option.value);

    expect(values).toEqual(["4", "5", "6", "7", "8"]);
  });

  it("출전마 수 변경 시 변경 콜백이 새 horseCount 값으로 호출된다", () => {
    const onSettingsChange = vi.fn();
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={0}
        onSettingsChange={onSettingsChange}
        onReset={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("출전마 수"), { target: { value: "7" } });

    expect(onSettingsChange).toHaveBeenCalledTimes(1);
    expect(onSettingsChange).toHaveBeenCalledWith({ horseCount: 7, muted: false });
  });

  it("음소거 토글 시 변경 콜백이 반전된 muted 값으로 호출된다", () => {
    const onSettingsChange = vi.fn();
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={0}
        onSettingsChange={onSettingsChange}
        onReset={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByLabelText("음소거"));

    expect(onSettingsChange).toHaveBeenCalledTimes(1);
    expect(onSettingsChange).toHaveBeenCalledWith({ horseCount: 5, muted: true });
  });

  it("파산 횟수가 화면에 노출된다", () => {
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={3}
        onSettingsChange={vi.fn()}
        onReset={vi.fn()}
      />,
    );

    expect(screen.getByText("파산 횟수: 3")).toBeTruthy();
  });

  it("초기화 버튼을 눌러도 곧바로 초기화 콜백이 호출되지 않는다", () => {
    const onReset = vi.fn();
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={0}
        onSettingsChange={vi.fn()}
        onReset={onReset}
      />,
    );

    fireEvent.click(screen.getByText("데이터 초기화"));

    expect(onReset).not.toHaveBeenCalled();
  });

  it("확인 단계에서 확인을 선택하면 초기화 콜백이 1회 호출된다", () => {
    const onReset = vi.fn();
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={0}
        onSettingsChange={vi.fn()}
        onReset={onReset}
      />,
    );

    fireEvent.click(screen.getByText("데이터 초기화"));
    fireEvent.click(screen.getByText("확인"));

    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it("확인 단계에서 취소를 선택하면 초기화 콜백이 호출되지 않는다", () => {
    const onReset = vi.fn();
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={0}
        onSettingsChange={vi.fn()}
        onReset={onReset}
      />,
    );

    fireEvent.click(screen.getByText("데이터 초기화"));
    fireEvent.click(screen.getByText("취소"));

    expect(onReset).not.toHaveBeenCalled();
    expect(screen.queryByText("확인")).toBeNull();
  });

  // T19 REVIEW 이월 메모 해소(T20c): 확인 경로에서도 인라인 확인 영역이 닫히고 복귀하는지 고정한다.
  it("확인을 선택하면 확인 영역이 닫히고 데이터 초기화 버튼이 복귀한다", () => {
    render(
      <SettingsPanel
        settings={SETTINGS}
        bankruptcyCount={0}
        onSettingsChange={vi.fn()}
        onReset={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText("데이터 초기화"));
    fireEvent.click(screen.getByText("확인"));

    expect(screen.queryByText("확인")).toBeNull();
    expect(screen.getByText("데이터 초기화")).toBeTruthy();
  });
});
