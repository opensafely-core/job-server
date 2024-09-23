/* eslint-disable no-console */
import userEvent from "@testing-library/user-event";
import React from "react";
import { ToastContainer } from "react-toastify";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";
import PrepareButton from "../../../components/Button/PrepareButton";
import * as useFileList from "../../../hooks/use-file-list";
import { fileList } from "../../helpers/files";
import props, { prepareUrl } from "../../helpers/props";
import { render, screen, waitFor } from "../../test-utils";

describe("<PrepareButton />", () => {
  const urls = {
    redirect: "http://localhost/prepare-redirect",
  };

  const { authToken, csrfToken, filesUrl } = props;

  const fileIds = ["abc1", "abc2", "abc3", "abc4"];

  beforeAll(() => {
    global.window = Object.create(window);
    Object.defineProperty(window, "location", {
      value: {
        ...window.location,
      },
      writable: true,
    });
  });

  afterAll(() => {
    vi.resetAllMocks();
  });

  it("hides the element if there are no files", () => {
    vi.spyOn(useFileList, "default").mockImplementation(() => ({
      data: [],
    }));

    const { container } = render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("shows if there are files", () => {
    vi.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />,
    );

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a draft publication",
    );
  });

  it("triggers a mutation on click", async () => {
    const user = userEvent.setup();
    vi.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    fetch.mockResponseOnce(async (req) => {
      const jsonBody = await req.json();
      expect(jsonBody.file_ids).toEqual(fileIds);

      return new Promise((resolve) =>
        // eslint-disable-next-line no-promise-executor-return
        setTimeout(() => {
          const res = { url: urls.redirect };
          return resolve(JSON.stringify(res));
        }, 10),
      );
    });
    render(
      <PrepareButton
        authToken={authToken}
        csrfToken={csrfToken}
        filesUrl={filesUrl}
        prepareUrl={prepareUrl}
      />,
    );

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a draft publication",
    );

    await user.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(screen.getByRole("button")).toHaveTextContent("Creating…"),
    );

    await waitFor(() => {
      expect(window.location.href).toEqual(urls.redirect);
    });
  });

  it("show the JSON error message", async () => {
    const user = userEvent.setup();
    console.error = vi.fn();

    vi.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    fetch.mockRejectOnce(new Error("Invalid user token"));

    render(
      <>
        <ToastContainer />
        <PrepareButton
          authToken={authToken}
          csrfToken={csrfToken}
          filesUrl={filesUrl}
          prepareUrl={prepareUrl}
        />
      </>,
    );

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a draft publication",
    );

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Error: Invalid user token",
    );
  });

  it("show the server error message", async () => {
    const user = userEvent.setup();
    console.error = vi.fn();

    vi.spyOn(useFileList, "default").mockImplementation(() => ({
      data: fileList,
    }));

    fetch.mockRejectOnce(new Error());

    render(
      <>
        <ToastContainer />
        <PrepareButton
          authToken={authToken}
          csrfToken={csrfToken}
          filesUrl={filesUrl}
          prepareUrl={prepareUrl}
        />
      </>,
    );

    expect(screen.getByRole("button")).toHaveTextContent(
      "Create a draft publication",
    );

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("alert")).toHaveTextContent("Error");
  });
});
