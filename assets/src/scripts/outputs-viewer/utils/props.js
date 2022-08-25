import PropTypes from "prop-types";

export const datasetProps = {
  authToken: PropTypes.string,
  basePath: PropTypes.string,
  csrfToken: PropTypes.string,
  filesUrl: PropTypes.string,
  prepareUrl: PropTypes.string,
  publishUrl: PropTypes.string,
  reviewUrl: PropTypes.string,
};

export const selectedFileProps = {
  date: PropTypes.string,
  id: PropTypes.string,
  is_deleted: PropTypes.bool,
  name: PropTypes.string,
  sha256: PropTypes.string,
  shortName: PropTypes.string,
  size: PropTypes.number,
  url: PropTypes.string,
  user: PropTypes.string,
  metadata: PropTypes.object,
};
