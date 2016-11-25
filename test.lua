#!/usr/bin/env th
require 'xlua'
require 'optim'
require 'nn'
require 'image'
require 'cunn'
require 'gnuplot'

local eye = 32

function img_resize(path)
    -- resize input/label
    local img = image.scale(image.load(path, 3), '^'..eye)
    local tx = math.floor((img:size(3)-eye)/2) + 1
    local ly = math.floor((img:size(2)-eye)/2) + 1
    img = img[{{},{ly,ly+eye-1},{tx,tx+eye-1}}]
    return img:cuda()
end

img_dir = './data/AdviceAnimals/AdviceAnimals2'
features = torch.Tensor(2):fill(string.byte('pics'))
features = features:cat(torch.Tensor(2):fill(10), 2)
image = img_resize(img_dir)
image = image:view(1, image:size(1), image:size(2), image:size(3))
image = image:cat(image, 1)
local model = torch.load('model.net'):cuda()
print(model)
model:evaluate()
output = model:forward(image:cuda())

print (output)
