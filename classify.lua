#!/usr/bin/env th
require 'xlua'
require 'optim'
require 'nn'
require 'image'
require 'cunn'
require 'gnuplot'
require 'loadcaffe'
--dofile './provider.lua'
local Provider = torch.class 'Provider'

torch.setdefaulttensortype('torch.FloatTensor')
torch.manualSeed(300)
local eye = 224              -- small net requires 231x231

model_dir = '../Adversarial_Examples/'
local model = loadcaffe.load(model_dir..'VGG_ILSVRC_19_layers_deploy.prototxt', model_dir..'VGG_ILSVRC_19_layers.caffemodel', 'nn'):cuda()  
print(model)
local file_results = io.open("results.txt", "w")

function img_resize(img_path)
    -- resize input/label
    local img = image.scale(image.load(img_path,3), '^'..eye)
    local tx = math.floor((img:size(3)-eye)/2) + 1
    local ly = math.floor((img:size(2)-eye)/2) + 1
    img = img[{{},{ly,ly+eye-1},{tx,tx+eye-1}}]
    --img:add(-mean):div(std)
    --switch to BGR
    local clone = img:clone()
    img[1] = clone[3]:add(-103.939/255)
    img[2] = clone[2]:add(-116.779/255)
    img[3] = clone[1]:add(-123.68/255)
    --vgg pixel range [0,255]
    img:mul(255)
    img = img:cuda()
    return img
end
local dir_path = './data/'
total_labels = torch.Tensor(1000):fill(0)
-- create a table of directories paths
local paths  = {}
f = io.popen('ls '.. dir_path)
for sub in f:lines() do
    table.insert(paths, dir_path..sub)
end

-- create a table of image paths
for key, sub_path in pairs(paths) do
    local total_labels = torch.Tensor(1000):fill(0)
    print(sub_path)
    local images = nil
    local images_path = {}
    f = io.popen('ls '.. sub_path)
    for image in f:lines() do
        if string.find(image, '.txt') == nil then
            --table.insert(images_path, sub_path..'/'..image)
            local temp_img = img_resize(sub_path..'/'..image)
            temp_img = temp_img:view(1, temp_img:size(1), temp_img:size(2), temp_img:size(3))
            local predict = model:forward(temp_img:cuda())
            local value, index = torch.sort(predict, true)
            total_labels[index[1][1]] = total_labels[index[1][1]]+1
        end
    end
    local confidences, indices = torch.sort(total_labels, true)
    --value, index = total_labels:max(total_labels:dim())
    print(indices[1], indices[2], indices[3])
end
value, index = total_labels:max(total_labels:dim())
file_results:close()



local file = io.open(model_dir.."vgg_labels.txt", "r");
local label = {}
for line in file:lines() do
    table.insert (label, line);
end

function test()
	model:evaluate()
    total_labels = nil
	local indices = torch.randperm(train_images:size(1)):long():split(10)
	-- remove last element so that all the batches have equal size
	indices[#indices] = nil
	for t,v in ipairs(indices) do
		xlua.progress(t, #indices)
		local inputs = train_images:index(1,v):cuda()
        local outputs = model:forward(inputs)
        if total_labels == nil then
            total_labels = outputs:clone()
        else
            total_labels = total_labels:add(output)
        end
	end
    print(total_labels)
end
--test()
