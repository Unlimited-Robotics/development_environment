ARG FROM

#### BUILDER Stage

FROM ${FROM} AS builder

ARG REPOS_LIST
ARG PACKAGES_LIST

# Copy ROS Packages
COPY / /robot/src_temp

# Build ROS Packages
RUN if [ -n "${REPOS_LIST// /}" ] && [ -n "${PACKAGES_LIST// /}" ]; then \
        cd /robot/src_temp && \
        mkdir /robot/src && \
        mv ${REPOS_LIST} /robot/src && \
        cd /robot && \
        rm -r /robot/src_temp && \
        /robot/scripts/build.ros.pkgs --packages-list ${PACKAGES_LIST}; \
    else \
        mkdir /robot/build; \
    fi

# #### PRODUCTION Stage

FROM ${FROM} AS production

ARG REPO_METADATA
ARG COMPONENT_METADATA
ARG REPO_NAME
ARG COMPONENT_NAME

# Copy binaries from builder
COPY --from=builder /robot/build /robot/build

# Copy Commands
COPY /${REPO_NAME}/components/${COMPONENT_NAME}/commands /robot/commands
COPY /${REPO_NAME}/components/${COMPONENT_NAME}/component_static_data /robot/component_static_data

# Labels
LABEL REPO_NAME=${REPO_NAME}
LABEL COMPONENT_NAME=${COMPONENT_NAME}
LABEL REPO_METADATA=${REPO_METADATA}
LABEL COMPONENT_METADATA=${COMPONENT_METADATA}
