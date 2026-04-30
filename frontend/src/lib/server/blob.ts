import { env } from '$env/dynamic/private';
import { BlobServiceClient, StorageSharedKeyCredential } from '@azure/storage-blob';

let serviceClient: BlobServiceClient | null = null;

function getServiceClient(): BlobServiceClient {
  if (serviceClient) return serviceClient;
  const account = env.STORAGE_ACCOUNT_NAME;
  const key = env.STORAGE_ACCOUNT_KEY;
  if (!account || !key) throw new Error('STORAGE_ACCOUNT_NAME / STORAGE_ACCOUNT_KEY not set');
  const cred = new StorageSharedKeyCredential(account, key);
  serviceClient = new BlobServiceClient(`https://${account}.blob.core.windows.net`, cred);
  return serviceClient;
}

export async function uploadImage(opts: {
  buffer: Buffer;
  contentType: string;
  blobName: string;
}): Promise<string> {
  const containerName = env.STORAGE_UPLOAD_CONTAINER || 'flowquote-uploads';
  const container = getServiceClient().getContainerClient(containerName);
  const block = container.getBlockBlobClient(opts.blobName);
  await block.uploadData(opts.buffer, {
    blobHTTPHeaders: { blobContentType: opts.contentType, blobCacheControl: 'public, max-age=31536000, immutable' }
  });
  return block.url;
}
