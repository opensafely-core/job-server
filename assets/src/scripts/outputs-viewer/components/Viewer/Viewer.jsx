import PropTypes from "prop-types";
import React from "react";
import useFile from "../../hooks/use-file";
import {
  canDisplay,
  isCsv,
  isHtml,
  isImg,
  isJson,
  isTxt,
} from "../../utils/file-type-match";
import { datasetProps, selectedFileProps } from "../../utils/props";
import Iframe from "../Iframe/Iframe";
import Image from "../Image/Image";
import NoPreview from "../NoPreview/NoPreview";
import Table from "../Table/Table";
import Text from "../Text/Text";
import Wrapper from "./Wrapper";

function Viewer({ authToken, selectedFile, uuid }) {
  const { data, error, isLoading, isError } = useFile(
    { authToken, selectedFile, uuid },
    {
      enabled: !!(selectedFile.url && canDisplay(selectedFile)),
    }
  );

  if (isLoading) {
    return (
      <Wrapper selectedFile={selectedFile}>
        <span>Loading...</span>
      </Wrapper>
    );
  }

  if (isError || !data) {
    return (
      <Wrapper selectedFile={selectedFile}>
        <NoPreview error={error} selectedFile={selectedFile} />
      </Wrapper>
    );
  }

  const incompatibleFileType = !canDisplay(selectedFile);
  const emptyData =
    (data && Object.keys(data).length === 0 && data.constructor === Object) ||
    data.size === 0;

  if (incompatibleFileType || emptyData) {
    return (
      <Wrapper selectedFile={selectedFile}>
        <NoPreview error={error} selectedFile={selectedFile} />
      </Wrapper>
    );
  }

  return (
    <Wrapper selectedFile={selectedFile}>
      {isCsv(selectedFile) ? <Table data={data} /> : null}
      {isHtml(selectedFile) && (
        <Iframe data={data} selectedFile={selectedFile} />
      )}
      {isImg(selectedFile) ? <Image data={data} /> : null}
      {isTxt(selectedFile) ? <Text data={data} /> : null}
      {isJson(selectedFile) ? <Text data={data} /> : null}
    </Wrapper>
  );
}

export default Viewer;

Viewer.propTypes = {
  authToken: datasetProps.authToken.isRequired,
  selectedFile: PropTypes.shape(selectedFileProps).isRequired,
  uuid: PropTypes.number.isRequired,
};
