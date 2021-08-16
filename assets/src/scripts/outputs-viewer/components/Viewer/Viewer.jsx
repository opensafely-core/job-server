import PropTypes from "prop-types";
import React from "react";
import useFile from "../../hooks/use-file";
import useStore from "../../stores/use-store";
import {
  canDisplay,
  isCsv,
  isHtml,
  isImg,
  isJson,
  isTxt,
} from "../../utils/file-type-match";
import Iframe from "../Iframe/Iframe";
import Image from "../Image/Image";
import Metadata from "../Metadata/Metadata";
import NoPreview from "../NoPreview/NoPreview";
import Table from "../Table/Table";
import Text from "../Text/Text";

function Wrapper({ children }) {
  return (
    <>
      <div className="card">
        <div className="card-header">
          <Metadata />
        </div>
        <div className="card-body">{children}</div>
      </div>
    </>
  );
}

function Viewer() {
  const { file } = useStore();
  const { data, error, isLoading, isError } = useFile(file, {
    enabled: !!(file.url && canDisplay(file)),
  });

  if (!file.url) return null;

  if (isLoading) {
    return (
      <Wrapper>
        <span>Loading...</span>
      </Wrapper>
    );
  }

  if (isError || !data) {
    return (
      <Wrapper>
        <NoPreview error={error} />
      </Wrapper>
    );
  }

  const incompatibleFileType = !canDisplay(file);
  const emptyData =
    data && Object.keys(data).length === 0 && data.constructor === Object;

  if (incompatibleFileType || emptyData) {
    return (
      <Wrapper>
        <NoPreview error={error} />
      </Wrapper>
    );
  }

  return (
    <Wrapper>
      {isCsv(file) ? <Table data={data} /> : null}
      {isHtml(file) ? <Iframe data={data} /> : null}
      {isImg(file) ? <Image data={data} /> : null}
      {isTxt(file) || isJson(file) ? <Text data={data} /> : null}
    </Wrapper>
  );
}

Wrapper.propTypes = {
  children: PropTypes.node.isRequired,
};

export default Viewer;
