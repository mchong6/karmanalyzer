require 'nn'
require 'image'
require 'xlua'
require 'cunn'


local Provider = torch.class 'Provider'
dir_path = "./data/"
images = nil
labels = nil
feature_dir = nil
feature_time = nil
local eye = 32

function img_resize(path)
    -- resize input/label
    local img = image.scale(image.load(path, 3), '^'..eye)
    local tx = math.floor((img:size(3)-eye)/2) + 1
    local ly = math.floor((img:size(2)-eye)/2) + 1
    img = img[{{},{ly,ly+eye-1},{tx,tx+eye-1}}]
    return img:cuda()
end

-- create a table of directories paths
local paths  = {}
f = io.popen('ls '.. dir_path)
for sub in f:lines() do
    table.insert(paths, dir_path..sub)
end

-- create a table of image paths
for key, sub_path in pairs(paths) do
    local images_path = {}
    f = io.popen('ls '.. sub_path)
    for image in f:lines() do
        if string.find(image, '.txt') ~= nil then
            -- update labels
            local label_file = io.open(sub_path..'/'..image, "r")
            for line in label_file:lines() do
                local var = {}
                for i in string.gmatch(line, "%S+") do
                    table.insert(var, i)
                end
                --strip the .txt extension
                local one =string.byte(image:sub(1, image:find("txt")-2))
                local two = tonumber(var[2])

                if labels == nil then
                    labels = torch.CudaTensor(1):fill(tonumber(var[1]))
                    feature_dir = torch.CudaTensor(1):fill(one)
                    feature_time = torch.CudaTensor(1):fill(two)
                else
                    labels = labels:cat(torch.CudaTensor(1):fill(tonumber(var[1])), 1)
                    feature_dir = feature_dir:cat(torch.CudaTensor(1):fill(one), 1)
                    feature_time = feature_time:cat(torch.CudaTensor(1):fill(two), 1)
                end
            end
        else
            -- get image paths
            table.insert(images_path, sub_path..'/'..image)
        end
    end
    --resize all images and store in a tensor.
    for key, image in pairs(images_path) do
        --resize to batch
        local temp_img = img_resize(image)
        temp_img = temp_img:view(1, temp_img:size(1), temp_img:size(2), temp_img:size(3))
        if images == nil then
            images = torch.CudaTensor(temp_img)
        else
            images = images:cat(torch.CudaTensor(temp_img), 1)
        end
    end
end
local other_features = torch.cat(feature_dir, feature_time, 2)

function Provider:__init(full)
  local trsize = images:size(1)
  local tesize = 1000


-- load dataset
self.trainData = {
 data = torch.Tensor(trsize, 3*eye*eye),
 data_feature = torch.Tensor(trsize, 2),
 labels = torch.Tensor(images:size(1)),
 size = function() return trsize end
}

local trainData = self.trainData
trainData.data = images:double()
trainData.data_feature = other_features
trainData.labels = labels

end

function Provider:normalize()
  ----------------------------------------------------------------------
  -- preprocess/normalize train/test sets
  --
  local trainData = self.trainData
  local testData = self.testData

  print '<trainer> preprocessing data (color space + normalization)'
  collectgarbage()

  -- preprocess trainSet
  local normalization = nn.SpatialContrastiveNormalization(1, image.gaussian1D(7))
  for i = 1,trainData:size() do
     xlua.progress(i, trainData:size())
     -- rgb -> yuv
     local rgb = trainData.data[i]
     local yuv = image.rgb2yuv(rgb)
     print(#yuv)
     -- normalize y locally:
     yuv[1] = normalization(yuv[{{1}}])
     trainData.data[i] = yuv
  end
  -- normalize u globally:
  local mean_u = trainData.data:select(2,2):mean()
  local std_u = trainData.data:select(2,2):std()
  trainData.data:select(2,2):add(-mean_u)
  trainData.data:select(2,2):div(std_u)
  -- normalize v globally:
  local mean_v = trainData.data:select(2,3):mean()
  local std_v = trainData.data:select(2,3):std()
  trainData.data:select(2,3):add(-mean_v)
  trainData.data:select(2,3):div(std_v)

  trainData.mean_u = mean_u
  trainData.std_u = std_u
  trainData.mean_v = mean_v
  trainData.std_v = std_v

  -- preprocess testSet
  for i = 1,testData:size() do
    xlua.progress(i, testData:size())
     -- rgb -> yuv
     local rgb = testData.data[i]
     local yuv = image.rgb2yuv(rgb)
     -- normalize y locally:
     yuv[{1}] = normalization(yuv[{{1}}])
     testData.data[i] = yuv
  end
  -- normalize u globally:
  testData.data:select(2,2):add(-mean_u)
  testData.data:select(2,2):div(std_u)
  -- normalize v globally:
  testData.data:select(2,3):add(-mean_v)
  testData.data:select(2,3):div(std_v)
end
