import PropTypes from "prop-types";
import React from "react";
import useFile from "../../utils/use-file";
import Iframe from "../Iframe/Iframe";
import Image from "../Image/Image";
import Metadata from "../Metadata/Metadata";
import Table from "../Table/Table";
import Text from "../Text/Text";

function Viewer({ file }) {
  const isCsv = file.name.match(/.*\.(?:csv)$/i);
  const isHtml = file.name.match(/.*\.(?:html)$/i);
  const isImg = file.name.match(/.*\.(?:gif|jpg|jpeg|png|svg)$/i);
  const isTxt = file.name.match(/.*\.(?:txt)$/i);

  const { data, error, isLoading, isError } = useFile(file.url, {
    enabled: !!(file.url && (isHtml || isCsv || isTxt || isImg)),
  });

  if (!file.url) return null;

  if (!isHtml && !isCsv && !isTxt && !isImg) {
    return (
      <>
        <Metadata file={file} />
        <p>We cannot show a preview of this file</p>
      </>
    );
  }

  if (isLoading) {
    return (
      <>
        <Metadata file={file} />
        <span>Loading...</span>
      </>
    );
  }

  if (isError) {
    return (
      <>
        <Metadata file={file} />
        <span>Error: {error.message}</span>
      </>
    );
  }

  return (
    <>
      <Metadata file={file} />
      <div className="card">
        <div className="card-body">
          {isCsv ? <Table data={data} /> : null}
          {isHtml ? <Iframe data={data} fileUrl={file.url} /> : null}
          {isImg ? <Image fileUrl={file.url} /> : null}
          {isTxt ? <Text data={data} /> : null}
        </div>
      </div>
    </>
  );
}

Viewer.propTypes = {
  file: PropTypes.shape({
    name: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
  }).isRequired,
};

export default Viewer;
