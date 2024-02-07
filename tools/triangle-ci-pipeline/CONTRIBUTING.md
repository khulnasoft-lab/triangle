The Salsa CI project is a Debian open source project and welcomes contributions such as:
* Opening up new issues that address specific areas to improve the pipeline.
* Improving the documentation e.g. by explaining concepts better or adding missing information
* Solving open issues. Some issues have labels attached to them which have different meanings. This also means they have been triaged and it would be great to have them solved. Some labels are:
    * **`Accepting MR`** - The issue has been triaged and is worthy of solving so a meaningful Merge Request is welcome
    * **`Newcomer`** - Issue is a good first start in case you are new to the project.
    * **`Nice-To-Have`** - The issue is good to solve but not urgent

To contribute to Salsa CI, you must have a Salsa (Debian's Gitlab Instance) account. To create an account, please follow the instructions in the [Salsa Documentation](https://wiki.debian.org/Salsa/Doc#Users).

Proposed modifications to the Salsa CI's pipeline are done via merge requests. For that:

1. Fork the project and clone the fork on your local machine. **_Your fork's visibility should be set to 'Public' for the pipeline to be shown on the merge request._** Committing directly to the upstream default branch is not allowed. To clone your project, we recommend you use the SSH option. You can find instructions about how to interact with Salsa via SSH at [https://salsa.debian.org/help/topics/authentication/index.md](https://salsa.debian.org/help/topics/authentication/index.md).

1. After cloning, create a branch with a meaningful name. _(Your branch should be up to date with the upstream default branch.)_  For merge requests closing an issue, it is convenient to prefix the branch name with the issue's number. 
**Note: _The branch name is used as a staging tag on the generated images. Because of this, slashes (`/`) are not allowed, otherwise, CI will fail. Avoid branch names like `something/other`._**

1. Make necessary changes and commit. **Please sign every commit.** Debian relies on OpenPGP to guarantee the authenticity and integrity of contributions. If you are wondering how to sign commits, read [this condensed summary](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work).  
**Note:** *YAML files follow a two-space indentation. Scripts in other languages should
follow their language-wide coding style. To check for errors in your YAML files before pushing changes, you can make use of [yamllint](https://yamllint.readthedocs.io/en/stable/quickstart.html).*

1. If you are a new contributor, add your name and emails to the [CONTRIBUTORS](CONTRIBUTORS) list.

1. Once you are satisfied with your changes, push them to your fork's remote repository and create a Merge Request against the upstream default branch.

If your Merge Request needs testing not covered by the pipeline's CI, it is important to link the tests you have done in the MR description or comment section to speed up the review. There are different ways to test different scenarios. You can always ping fellow contributors to see how to carry out certain tests.

### Allow images to be persistent

Depending on how you have to test your Merge Request, you may want to allow images to persist. 
By default all generated images are deleted when the MR test pipeline is finished. This is to avoid images from
being created and stored in the registry when the project is forked.

To disable this behavior set the `SALSA_CI_PERSIST_IMAGES` to 1, 'yes' or
'true' on a CI variable (*CI/CD Settings*).
