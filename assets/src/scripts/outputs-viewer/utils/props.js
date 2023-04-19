import PropTypes from "prop-types";

export const datasetProps = {
  authToken: PropTypes.string,
  basePath: PropTypes.string,
  csrfToken: PropTypes.string,
  filesUrl: PropTypes.string,
  prepareUrl: PropTypes.string,
  publishUrl: PropTypes.string,
};

export const selectedFileProps = {
  date: PropTypes.string,
  id: PropTypes.string,
  is_deleted: PropTypes.bool,
  name: PropTypes.string,
  sha256: PropTypes.string,
  size: PropTypes.number,
  url: PropTypes.string,
  user: PropTypes.string,
};
