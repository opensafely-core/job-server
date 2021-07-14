import PropTypes from "prop-types";
import React from "react";
import useFile from "../../utils/use-file";
import Iframe from "../Iframe/Iframe";
import Image from "../Image/Image";
import Table from "../Table/Table";
import Text from "../Text/Text";

function Viewer({ fileUrl }) {
  if (!fileUrl || fileUrl === "") return null;

  const isCsv = fileUrl.match(/.*\.(?:csv)$/i);
  const isHtml = fileUrl.match(/.*\.(?:html)$/i);
  const isImg = fileUrl.match(/.*\.(?:gif|jpg|jpeg|png|svg)$/i);
  const isTxt = fileUrl.match(/.*\.(?:txt)$/i);

  if (!isHtml && !isCsv && !isTxt && !isImg) {
    return <p>We cannot show a preview of this file</p>;
  }

  const { data, error, isLoading, isError } = useFile(fileUrl);

  if (isLoading) return <span>Loading...</span>;

  if (isError) return <span>Error: {error.message}</span>;

  if (isCsv) return <Table data={data} />;

  if (isHtml) return <Iframe data={data} fileUrl={fileUrl} />;

  if (isImg) return <Image fileUrl={fileUrl} />;

  if (isTxt) return <Text data={data} />;
}

Viewer.propTypes = {
  fileUrl: PropTypes.string.isRequired,
};

export default Viewer;
