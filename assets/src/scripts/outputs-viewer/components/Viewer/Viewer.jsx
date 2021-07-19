import PropTypes from "prop-types";
import React from "react";
import {
  canDisplay,
  isCsv,
  isHtml,
  isImg,
  isTxt,
} from "../../utils/file-type-match";
import useFile from "../../utils/use-file";
import Iframe from "../Iframe/Iframe";
import Image from "../Image/Image";
import Metadata from "../Metadata/Metadata";
import Table from "../Table/Table";
import Text from "../Text/Text";

function Wrapper({ children, file }) {
  return (
    <>
      <Metadata file={file} />
      <div className="card">
        <div className="card-body">{children}</div>
      </div>
    </>
  );
}

function Viewer({ file }) {
  const { data, error, isLoading, isError } = useFile(file, {
    enabled: !!(file.url && canDisplay(file)),
  });

  if (!file.url) return null;

  if (isLoading) {
    return (
      <Wrapper file={file}>
        <span>Loading...</span>
      </Wrapper>
    );
  }

  if (isError) {
    return (
      <Wrapper file={file}>
        <span>Error: {error.message}</span>
      </Wrapper>
    );
  }

  const incompatibleFileType = !canDisplay(file);
  const emptyData =
    data && Object.keys(data).length === 0 && data.constructor === Object;

  if (incompatibleFileType || emptyData) {
    return (
      <Wrapper file={file}>
        <p>We cannot show a preview of this file.</p>
        <p>
          <a href={file.url} rel="noreferrer noopener" target="filePreview">
            Open file in a new tab &#8599;
          </a>
        </p>
      </Wrapper>
    );
  }

  return (
    <Wrapper file={file}>
      {isCsv(file) ? <Table data={data} /> : null}
      {isHtml(file) ? <Iframe data={data} fileUrl={file.url} /> : null}
      {isImg(file) ? <Image fileUrl={file.url} /> : null}
      {isTxt(file) ? <Text data={data} /> : null}
    </Wrapper>
  );
}

Wrapper.propTypes = {
  children: PropTypes.node.isRequired,
  file: PropTypes.shape({
    name: PropTypes.string.isRequired,
    size: PropTypes.number.isRequired,
    url: PropTypes.string.isRequired,
  }).isRequired,
};

Viewer.propTypes = {
  file: PropTypes.shape({
    name: PropTypes.string,
    size: PropTypes.number,
    url: PropTypes.string,
  }).isRequired,
};

export default Viewer;
