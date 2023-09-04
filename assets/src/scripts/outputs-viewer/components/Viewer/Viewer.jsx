import { useQuery } from "@tanstack/react-query";
import PropTypes from "prop-types";
import React from "react";
import {
  canDisplay,
  isCsv,
  isHtml,
  isImg,
  isJson,
  isNotUploadedStr,
  isTxt,
} from "../../utils/file-type-match";
import { datasetProps, selectedFileProps } from "../../utils/props";
import { toastError } from "../../utils/toast";
import Iframe from "../Iframe/Iframe";
import Image from "../Image/Image";
import Link from "../Link";
import NoPreview from "../NoPreview/NoPreview";
import Table from "../Table/Table";
import Text from "../Text/Text";

function Viewer({ authToken, fileName, fileSize, fileUrl, uuid }) {
  const { data, error, isLoading, isError } = useQuery(
    ["FILE", fileUrl],
    async () => {
      // If we can't display the file type
      // or the file size is too large (>20mb)
      // don't try to return the data
      if (!canDisplay(fileName) || fileSize > 20000000) return false;

      // If the file is a CSV
      // and the file size is too large (>5mb)
      // don't try to return the data
      if (isCsv(fileName) && fileSize > 5000000) return false;

      // Combine file URL with UUID
      const fileURL = `${fileUrl}?${uuid}`;

      let response = await fetch(fileURL, {
        headers: {
          Authorization: authToken,
        },
      });

      if (!response.ok) throw new Error();

      // check if redirected to release-hatch for an un-uploaded file
      if (
        response.headers.has("Location") &&
        response.headers.has("Authorization")
      ) {
        response = await fetch(response.headers.get("Location"), {
          headers: {
            Authorization: response.headers.get("Authorization"),
          },
        });
        if (!response.ok) throw new Error();
      }

      // If the text matches the not uploaded string,
      // return early with that text
      const bodyText = await response.clone().text();
      if (bodyText === isNotUploadedStr) return isNotUploadedStr;

      // If the file is an image
      // grab the blob and create a URL for the blob
      if (isImg(fileName)) {
        const blob = await response.blob();
        return URL.createObjectURL(blob);
      }

      // Otherwise return the text of the data
      return bodyText;
    },
    {
      onError: () => {
        toastError({
          fileUrl,
          message: `${fileName} - Unable to load file`,
          toastId: fileUrl,
          url: document.location.href,
        });
      },
    },
  );

  if (isLoading) {
    return <span>Loading...</span>;
  }

  if (data === isNotUploadedStr) {
    return (
      <>
        <p>
          This file has not been uploaded yet. This is likely due to do an error
          that occurred during release.
        </p>
        <p className="mt-3">
          <Link
            href="https://docs.opensafely.org/how-to-get-help/#slack"
            newTab
          >
            Contact tech support in Slack for more information.
          </Link>
        </p>
      </>
    );
  }

  if (isError || !data || !canDisplay(fileName)) {
    return <NoPreview error={error} fileUrl={fileUrl} />;
  }

  return (
    <>
      {isCsv(fileName) ? <Table data={data} /> : null}
      {isHtml(fileName) && (
        <Iframe data={data} fileName={fileName} fileUrl={fileUrl} />
      )}
      {isImg(fileName) ? <Image data={data} /> : null}
      {isTxt(fileName) ? <Text data={data} /> : null}
      {isJson(fileName) ? <Text data={data} /> : null}
    </>
  );
}

export default Viewer;

Viewer.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  fileName: selectedFileProps.name.isRequired,
  fileSize: selectedFileProps.size.isRequired,
  fileUrl: selectedFileProps.url.isRequired,
  uuid: PropTypes.number.isRequired,
};
