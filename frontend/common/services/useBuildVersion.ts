import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { Version } from 'common/types/responses'
import Project from 'common/project'
import { StoreStateType } from 'common/store'
import data from 'common/data/base/_data'
export const defaultVersionTag = 'Unknown'
export const buildVersionService = service
  .enhanceEndpoints({ addTagTypes: ['BuildVersion'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getBuildVersion: builder.query<Version, Req['getBuildVersion']>({
        providesTags: () => [{ id: 'BuildVersion', type: 'BuildVersion' }],
        queryFn: async (args, _, _2, baseQuery) => {
          try {
            const [frontendRes, backendRes] = await Promise.all([
              data.get(`/version/`).catch(() => ({})),
              data.get(`${Project.api.replace('api/v1/', '')}version/`),
            ])

            const frontend = (frontendRes || {}) as Version['frontend']
            const backend =
              (backendRes as Version['backend']) || ({} as Version['backend'])

            const tag = backend?.image_tag || defaultVersionTag
            const backend_sha = backend?.ci_commit_sha || defaultVersionTag
            const frontend_sha = frontend?.ci_commit_sha || defaultVersionTag

            const result: Version = {
              backend,
              backend_sha,
              frontend,
              frontend_sha,
              tag,
            }

            return { data: result }
          } catch (error) {
            return {
              error: {
                error: error instanceof Error ? error.message : String(error),
                status: 'VERSION_FETCH_ERROR',
              },
            }
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getBuildVersion(
  store: any,
  data: Req['getBuildVersion'],
  options?: Parameters<
    typeof buildVersionService.endpoints.getBuildVersion.initiate
  >[1],
) {
  return store.dispatch(
    buildVersionService.endpoints.getBuildVersion.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const selectBuildVersion = (state: StoreStateType) =>
  buildVersionService.endpoints.getBuildVersion.select({})(state)?.data

export const {
  useGetBuildVersionQuery,
  // END OF EXPORTS
} = buildVersionService

/* Usage examples:
const { data, isLoading } = useGetBuildVersionQuery({ id: 2 }, {}) //get hook
const [createBuildVersion, { isLoading, data, isSuccess }] = useCreateBuildVersionMutation() //create hook
buildVersionService.endpoints.getBuildVersion.select({id: 2})(store.getState()) //access data from any function
*/
